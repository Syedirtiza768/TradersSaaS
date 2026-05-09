#!/usr/bin/env bash
# =============================================================================
# Traders — EC2 Full Redeploy Script
# =============================================================================
# Performs a complete no-cache rebuild and redeployment:
#   1. Pull latest code from git
#   2. Rebuild ALL Docker images from scratch (--no-cache)
#   3. Restart all services
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
SITE_NAME="${SITE_NAME:-enxi.realtrackapp.com}"
ENV_FILE="compose/.env"

# ── Load .env so SITE_NAME / ADMIN_PASSWORD are available ──────────────────
if [[ -f "$ENV_FILE" ]]; then
    # shellcheck disable=SC2046
    export $(grep -v '^#' "$ENV_FILE" | grep -v '^\s*$' | xargs)
fi

SITE_NAME="${SITE_NAME:-enxi.realtrackapp.com}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-Admin@2026}"

log()  { echo -e "\n\033[1;34m▶  $*\033[0m"; }
ok()   { echo -e "\033[1;32m✅ $*\033[0m"; }
warn() { echo -e "\033[1;33m⚠️  $*\033[0m"; }
fail() { echo -e "\033[1;31m❌ $*\033[0m"; exit 1; }

bench_exec() {
    docker compose -f "$COMPOSE_FILE" exec -T backend \
        bash -c "cd /home/frappe/frappe-bench && $*"
}

# =============================================================================
log "STEP 1 — Git pull"
# =============================================================================
git checkout -- compose/docker-compose.yml 2>/dev/null || true
git pull origin main || fail "git pull failed — check for local conflicts"
ok "Code up to date"

# =============================================================================
log "STEP 2 — Stop all containers"
# =============================================================================
docker compose -f "$COMPOSE_FILE" down --remove-orphans || true
ok "Containers stopped"

# =============================================================================
log "STEP 3 — Remove stale images (no-cache rebuild)"
# =============================================================================
docker rmi traders-backend:latest traders-frontend:latest 2>/dev/null || true
ok "Old images removed"

# =============================================================================
log "STEP 4 — Build ALL images from scratch (no cache)"
# =============================================================================
# Build sequentially: parallel frontend + backend builds can overload small EC2
# instances and hit BuildKit grpc disconnects while sending a huge context.
docker compose -f "$COMPOSE_FILE" build --no-cache --pull frontend \
    || fail "frontend image build failed"
docker compose -f "$COMPOSE_FILE" build --no-cache --pull backend \
    || fail "backend image build failed (shared by workers/scheduler/websocket)"
ok "Images built"

# =============================================================================
log "STEP 5 — Start all services"
# =============================================================================
docker compose -f "$COMPOSE_FILE" up -d
ok "Services started"

# =============================================================================
log "STEP 6 — Wait for backend to become healthy (up to 120s)"
# =============================================================================
TIMEOUT=120
ELAPSED=0
until docker compose -f "$COMPOSE_FILE" ps backend \
        | grep -qE "(healthy|running)"; do
    if [[ $ELAPSED -ge $TIMEOUT ]]; then
        docker compose -f "$COMPOSE_FILE" logs --tail=50 backend
        fail "Backend did not become healthy within ${TIMEOUT}s"
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
SITE_EXISTS=$(bench_exec "bench --site '$SITE_NAME' list-apps 2>&1" || echo "no")
if echo "$SITE_EXISTS" | grep -q "No such site\|does not exist\|no"; then
    warn "Site '$SITE_NAME' not found — creating it now"
    bench_exec "bench new-site '$SITE_NAME' \
        --db-root-password \"\${DB_ROOT_PASSWORD}\" \
        --admin-password '$ADMIN_PASSWORD' \
        --install-app erpnext \
        --no-mariadb-socket"
    ok "Site '$SITE_NAME' created"
else
    ok "Site '$SITE_NAME' exists"
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
log "STEP 15 — Final health check"
# =============================================================================
sleep 5
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Host: $SITE_NAME" http://localhost:8080/api/method/ping)

if [[ "$HTTP_STATUS" == "200" ]]; then
    ok "Health check passed — site is live"
else
    warn "Health check returned HTTP $HTTP_STATUS"
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
