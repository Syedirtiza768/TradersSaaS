#!/usr/bin/env bash
# =============================================================================
# Traders — EC2 Full Redeploy Script
# =============================================================================
# Performs a full EC2 redeployment:
#   1. Pull latest code from git
#   2. Rebuild application Docker images
#   3. Start core services
#   4. Wait for backend health
#   5. Run bench migrate
#   6. Install trader_app on the site (if not already installed)
#   7. Seed demo data (company, users, customers, suppliers, items, transactions)
#
# Usage:
#   chmod +x scripts/redeploy-ec2.sh
#   cd /opt/traders && bash scripts/redeploy-ec2.sh
#
# Set SITE_NAME and ADMIN_PASSWORD in compose/.env before running.
# =============================================================================

set -euo pipefail

COMPOSE_FILE="compose/docker-compose.yml"
ENV_FILE="compose/.env"

# ── Load .env so SITE_NAME / ADMIN_PASSWORD are available ───────────────────
if [[ -f "$ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
fi

SITE_NAME="${SITE_NAME:-enxi.realtrackapp.com}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-Admin@2026}"
BUILD_ATTEMPTS="${BUILD_ATTEMPTS:-3}"
BUILD_RETRY_DELAY="${BUILD_RETRY_DELAY:-20}"
BACKEND_TIMEOUT="${BACKEND_TIMEOUT:-420}"
BUILD_PROGRESS="${BUILD_PROGRESS:-plain}"
# Step 16: API can return 504 until Gunicorn/Frappe finishes warming up after workers start.
HEALTH_RETRIES="${HEALTH_RETRIES:-12}"
HEALTH_RETRY_DELAY="${HEALTH_RETRY_DELAY:-10}"
CURL_MAX_TIME="${CURL_MAX_TIME:-30}"

log()  { echo -e "\n\033[1;34m▶  $*\033[0m"; }
ok()   { echo -e "\033[1;32m✅ $*\033[0m"; }
warn() { echo -e "\033[1;33m⚠️  $*\033[0m"; }
fail() { echo -e "\033[1;31m❌ $*\033[0m"; exit 1; }

retry() {
    local attempts="$1"
    local delay="$2"
    shift 2

    local attempt=1
    until "$@"; do
        if [[ "$attempt" -ge "$attempts" ]]; then
            return 1
        fi
        warn "Command failed; retrying in ${delay}s (${attempt}/${attempts})"
        sleep "$delay"
        attempt=$((attempt + 1))
    done
}

bench_exec() {
    docker compose -f "$COMPOSE_FILE" exec -T backend \
        bash -c "cd /home/frappe/frappe-bench && $*"
}

# =============================================================================
log "STEP 1 — Git pull"
# =============================================================================
git pull --ff-only origin main || fail "git pull failed — check for local conflicts"
ok "Code up to date"

# =============================================================================
log "STEP 2 — Stop all containers"
# =============================================================================
docker compose -f "$COMPOSE_FILE" down --remove-orphans || true
ok "Containers stopped"

# =============================================================================
log "STEP 3 — Prepare Docker build"
# =============================================================================
BUILD_FLAGS=()
if [[ "${NO_CACHE:-0}" == "1" || "${NO_CACHE:-false}" == "true" ]]; then
    BUILD_FLAGS+=(--no-cache)
fi
if [[ "${PULL_BASE_IMAGES:-0}" == "1" || "${PULL_BASE_IMAGES:-false}" == "true" ]]; then
    BUILD_FLAGS+=(--pull)
fi
ok "Build flags: ${BUILD_FLAGS[*]:-(default cache, no forced pull)}"

# =============================================================================
log "STEP 4 — Build application images"
# =============================================================================
# Build sequentially: parallel frontend + backend builds can overload small EC2
# instances and hit BuildKit grpc disconnects while sending a huge context.
log "STEP 4A — Build frontend image"
retry "$BUILD_ATTEMPTS" "$BUILD_RETRY_DELAY" \
    docker compose -f "$COMPOSE_FILE" build --progress "$BUILD_PROGRESS" "${BUILD_FLAGS[@]}" frontend \
    || fail "frontend image build failed"
ok "Frontend image built"

log "STEP 4B — Build backend image"
retry "$BUILD_ATTEMPTS" "$BUILD_RETRY_DELAY" \
    docker compose -f "$COMPOSE_FILE" build --progress "$BUILD_PROGRESS" "${BUILD_FLAGS[@]}" backend \
    || fail "backend image build failed (shared by workers/scheduler/websocket)"
ok "Backend image built"

# =============================================================================
log "STEP 5 — Start core services"
# =============================================================================
docker compose -f "$COMPOSE_FILE" up -d db redis-cache redis-queue frontend backend \
    || {
        docker compose -f "$COMPOSE_FILE" logs --tail=80 backend
        fail "Core services failed to start"
    }
ok "Core services started"

# =============================================================================
log "STEP 6 — Wait for backend to accept traffic (up to ${BACKEND_TIMEOUT}s)"
# =============================================================================
ELAPSED=0
until [[ "$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$(docker compose -f "$COMPOSE_FILE" ps -q backend)" 2>/dev/null || echo missing)" == "healthy" ]]; do
    STATUS="$(docker inspect -f '{{.State.Status}}' "$(docker compose -f "$COMPOSE_FILE" ps -q backend)" 2>/dev/null || echo missing)"
    if [[ "$STATUS" == "exited" || "$STATUS" == "dead" ]]; then
        docker compose -f "$COMPOSE_FILE" logs --tail=120 backend
        fail "Backend container exited before becoming healthy"
    fi
    if [[ $ELAPSED -ge $BACKEND_TIMEOUT ]]; then
        docker compose -f "$COMPOSE_FILE" ps
        docker compose -f "$COMPOSE_FILE" logs --tail=120 backend
        fail "Backend did not become healthy within ${BACKEND_TIMEOUT}s"
    fi
    echo "  waiting… ${ELAPSED}s"
    sleep 8
    ELAPSED=$((ELAPSED + 8))
done
ok "Backend is healthy"

# Give gunicorn workers a moment to fully start
sleep 5

# =============================================================================
log "STEP 7 — Verify site exists"
# =============================================================================
SITE_DIR_EXISTS=$(bench_exec "[ -d 'sites/$SITE_NAME' ] && echo yes || echo no")
SITE_APPS=$(bench_exec "bench --site '$SITE_NAME' list-apps 2>&1" || true)

if [[ "$SITE_DIR_EXISTS" == "yes" ]]; then
    ok "Site '$SITE_NAME' exists"
elif echo "$SITE_APPS" | grep -qi "No such site\|does not exist"; then
    warn "Site '$SITE_NAME' not found — creating it now"
    CREATE_SITE_OUTPUT=$(bench_exec "bench new-site '$SITE_NAME' \
        --db-root-password \"\${DB_ROOT_PASSWORD}\" \
        --admin-password '$ADMIN_PASSWORD' \
        --install-app erpnext \
        --mariadb-user-host-login-scope='%' 2>&1" || true)
    if echo "$CREATE_SITE_OUTPUT" | grep -qi "already exists"; then
        warn "Site '$SITE_NAME' already exists — continuing"
    elif echo "$CREATE_SITE_OUTPUT" | grep -qi "Traceback\|Error"; then
        echo "$CREATE_SITE_OUTPUT"
        fail "Site '$SITE_NAME' could not be created"
    else
        ok "Site '$SITE_NAME' created"
    fi
else
    warn "Could not verify site with list-apps; continuing because backend is running"
    echo "$SITE_APPS"
fi

# =============================================================================
log "STEP 8 — Install/upgrade ERPNext on site"
# =============================================================================
bench_exec "bench --site '$SITE_NAME' install-app erpnext 2>&1 || true"
ok "ERPNext checked"

# =============================================================================
log "STEP 9 — Install trader_app on site"
# =============================================================================
APPS=$(bench_exec "bench --site '$SITE_NAME' list-apps 2>&1")
if echo "$APPS" | grep -q "trader_app"; then
    ok "trader_app already installed on site"
else
    bench_exec "bench --site '$SITE_NAME' install-app trader_app"
    ok "trader_app installed"
fi

# =============================================================================
log "STEP 10 — Run migrations"
# =============================================================================
bench_exec "bench --site '$SITE_NAME' migrate --skip-failing || \
            bench --site '$SITE_NAME' migrate"
ok "Migrations done"

# =============================================================================
log "STEP 11 — Clear cache"
# =============================================================================
bench_exec "bench --site '$SITE_NAME' clear-cache"
bench_exec "bench --site '$SITE_NAME' clear-website-cache 2>/dev/null || true"
ok "Cache cleared"

# =============================================================================
log "STEP 12 — Ensure custom roles exist (after_install)"
# =============================================================================
bench_exec "bench --site '$SITE_NAME' execute \
    trader_app.setup.after_install"
ok "Roles created"

# =============================================================================
log "STEP 13 — Seed demo data"
# =============================================================================
# Check if demo user already exists to decide whether to skip seeding
DEMO_USER_EXISTS=$(bench_exec \
    "bench --site '$SITE_NAME' execute frappe.db.exists \
     --args '[\"User\", \"demo@globaltrading.pk\"]' 2>/dev/null" || echo "")

if echo "$DEMO_USER_EXISTS" | grep -q "demo@globaltrading.pk"; then
    ok "Demo data already present (demo user found) — skipping seed"
else
    log "Running demo installer (this takes 5–15 minutes)…"
    bench_exec "bench --site '$SITE_NAME' execute trader_app.demo.install_demo"
    ok "Demo data seeded"
fi

# =============================================================================
log "STEP 14 — Reset demo user password (ensure Demo@12345)"
# =============================================================================
bench_exec "bench --site '$SITE_NAME' execute \
    frappe.core.doctype.user.user.update_password \
    --args '[\"demo@globaltrading.pk\", \"Demo@12345\"]' 2>/dev/null || true"
# Also ensure Administrator password is set
bench_exec "bench --site '$SITE_NAME' set-admin-password '$ADMIN_PASSWORD' 2>/dev/null || true"
ok "Passwords set"

# =============================================================================
log "STEP 15 — Start workers, scheduler, websocket, and proxy"
# =============================================================================
docker compose -f "$COMPOSE_FILE" up -d worker-short worker-long worker-default scheduler websocket proxy \
    || {
        docker compose -f "$COMPOSE_FILE" ps
        docker compose -f "$COMPOSE_FILE" logs --tail=80 proxy backend
        fail "Application services failed to start"
    }
ok "Application services started"

# =============================================================================
log "STEP 16 — Final health check"
# =============================================================================
sleep 5
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$CURL_MAX_TIME" \
    -H "Host: $SITE_NAME" "http://localhost:${HTTP_PORT:-8080}/" \
    2>/dev/null || true)
FRONTEND_STATUS="${FRONTEND_STATUS:-000}"

API_STATUS="000"
for ((i = 1; i <= HEALTH_RETRIES; i++)); do
    API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$CURL_MAX_TIME" \
        -H "Host: $SITE_NAME" "http://localhost:${HTTP_PORT:-8080}/api/method/ping" \
        2>/dev/null || true)
    API_STATUS="${API_STATUS:-000}"
    if [[ "$API_STATUS" == "200" ]]; then
        break
    fi
    if [[ "$i" -lt "$HEALTH_RETRIES" ]]; then
        echo "  API ping attempt $i/$HEALTH_RETRIES: HTTP $API_STATUS — retrying in ${HEALTH_RETRY_DELAY}s…"
        sleep "$HEALTH_RETRY_DELAY"
    fi
done

if [[ "$FRONTEND_STATUS" == "200" && "$API_STATUS" == "200" ]]; then
    ok "Health check passed — site is live"
else
    warn "Health check returned frontend HTTP $FRONTEND_STATUS, API HTTP $API_STATUS"
    docker compose -f "$COMPOSE_FILE" ps
    docker compose -f "$COMPOSE_FILE" logs --tail=80 proxy frontend backend
fi

# =============================================================================
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              🚀 DEPLOYMENT COMPLETE                          ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Site:     https://$SITE_NAME"
echo "║"
echo "║  Demo Login:"
echo "║    Email:    demo@globaltrading.pk"
echo "║    Password: Demo@12345"
echo "║"
echo "║  Admin Login:"
echo "║    Email:    Administrator"
echo "║    Password: $ADMIN_PASSWORD"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

docker compose -f "$COMPOSE_FILE" ps
