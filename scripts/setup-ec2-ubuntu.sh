#!/usr/bin/env bash
# =============================================================================
# Traders — New Ubuntu EC2 bootstrap (Docker app + host nginx + Let's Encrypt)
# Domain default: enxi.realtrackapp.com
#
# Run on a fresh Ubuntu 22.04/24.04 EC2 instance (as a user with sudo):
#   curl -fsSL https://raw.githubusercontent.com/Syedirtiza768/traders/main/scripts/setup-ec2-ubuntu.sh -o setup-ec2-ubuntu.sh
#   chmod +x setup-ec2-ubuntu.sh
#   sudo DOMAIN=enxi.realtrackapp.com CERTBOT_EMAIL=you@example.com ./setup-ec2-ubuntu.sh
#
# Or after cloning the repo:
#   cd /opt/traders && sudo CERTBOT_EMAIL=you@example.com bash scripts/setup-ec2-ubuntu.sh
# =============================================================================

set -euo pipefail

DOMAIN="${DOMAIN:-enxi.realtrackapp.com}"
WWW_DOMAIN="www.${DOMAIN}"
REPO_DIR="${REPO_DIR:-/opt/traders}"
REPO_URL="${REPO_URL:-https://github.com/Syedirtiza768/traders.git}"
BRANCH="${BRANCH:-main}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-}"
SKIP_SSL="${SKIP_SSL:-0}"
SKIP_DEPLOY="${SKIP_DEPLOY:-0}"

log()  { echo -e "\n\033[1;34m▶  $*\033[0m"; }
ok()   { echo -e "\033[1;32m✅ $*\033[0m"; }
warn() { echo -e "\033[1;33m⚠️  $*\033[0m"; }
fail() { echo -e "\033[1;31m❌ $*\033[0m"; exit 1; }

if [[ "$(id -u)" -ne 0 ]]; then
    fail "Run with sudo: sudo CERTBOT_EMAIL=you@example.com $0"
fi

DEPLOY_USER="${SUDO_USER:-ubuntu}"
if ! id "$DEPLOY_USER" &>/dev/null; then
    DEPLOY_USER="ubuntu"
fi

# ── 1. System packages ───────────────────────────────────────────────────────
log "Installing Docker, nginx, certbot, git"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq ca-certificates curl git nginx certbot python3-certbot-nginx

if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
fi
apt-get install -y -qq docker-compose-plugin
usermod -aG docker "$DEPLOY_USER" || true
ok "Packages installed"

# ── 2. Clone repository ──────────────────────────────────────────────────────
log "Cloning repository to $REPO_DIR"
mkdir -p "$(dirname "$REPO_DIR")"
if [[ -d "$REPO_DIR/.git" ]]; then
    warn "Repo exists — pulling latest"
    git -C "$REPO_DIR" fetch origin "$BRANCH"
    git -C "$REPO_DIR" checkout "$BRANCH"
    git -C "$REPO_DIR" pull --ff-only origin "$BRANCH" || true
else
    git clone --branch "$BRANCH" --depth 1 "$REPO_URL" "$REPO_DIR"
fi
chown -R "$DEPLOY_USER:$DEPLOY_USER" "$REPO_DIR"
ok "Repository ready at $REPO_DIR"

# ── 3. Production .env ───────────────────────────────────────────────────────
log "Configuring compose/.env for $DOMAIN"
ENV_FILE="$REPO_DIR/compose/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    cp "$REPO_DIR/compose/.env.example" "$ENV_FILE"
fi

gen_secret() { openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 24; }

set_env() {
    local key="$1" val="$2"
    if grep -q "^${key}=" "$ENV_FILE"; then
        sed -i "s|^${key}=.*|${key}=${val}|" "$ENV_FILE"
    else
        echo "${key}=${val}" >> "$ENV_FILE"
    fi
}

set_env SITE_NAME "$DOMAIN"
set_env VITE_SITE_NAME "$DOMAIN"
set_env VITE_API_URL "https://${DOMAIN}/api"
set_env HTTP_PORT "8080"

if grep -qE '^(DB_ROOT_PASSWORD|ADMIN_PASSWORD)=.*(changeme|trader_db_root|TraderAdmin)' "$ENV_FILE" 2>/dev/null; then
    set_env DB_ROOT_PASSWORD "$(gen_secret)"
    set_env ADMIN_PASSWORD "$(gen_secret)"
    warn "Generated new DB_ROOT_PASSWORD and ADMIN_PASSWORD in $ENV_FILE"
fi

if ! grep -q '^ENCRYPTION_KEY=' "$ENV_FILE" || grep -q '^ENCRYPTION_KEY=a1b2' "$ENV_FILE"; then
    set_env ENCRYPTION_KEY "$(openssl rand -hex 32)"
fi
if ! grep -q '^SECRET_KEY=' "$ENV_FILE" || grep -q '^SECRET_KEY=trader_secret' "$ENV_FILE"; then
    set_env SECRET_KEY "$(openssl rand -base64 48)"
fi

chown "$DEPLOY_USER:$DEPLOY_USER" "$ENV_FILE"
ok "Environment file: $ENV_FILE"

# ── 4. Deploy application (Docker) ───────────────────────────────────────────
if [[ "$SKIP_DEPLOY" == "1" ]]; then
    warn "SKIP_DEPLOY=1 — skipping Docker deploy"
else
    log "Running full EC2 deploy (build + migrate; may take 20–40 min on first run)"
    sudo -u "$DEPLOY_USER" bash -lc "cd '$REPO_DIR' && bash scripts/redeploy-ec2.sh" \
        || fail "redeploy-ec2.sh failed — check logs: docker compose -f compose/docker-compose.yml logs"
    ok "Application stack is up on 127.0.0.1:8080"
fi

# ── 5. Host nginx (HTTP first) ───────────────────────────────────────────────
log "Configuring host nginx"
mkdir -p /var/www/certbot
cp "$REPO_DIR/infra/nginx/enxi.realtrackapp.com.http-only.conf" \
    "/etc/nginx/sites-available/${DOMAIN}"
# Use domain-specific filename even if DOMAIN was overridden
sed -i "s/enxi\.realtrackapp\.com/${DOMAIN}/g" "/etc/nginx/sites-available/${DOMAIN}"
sed -i "s/www\.enxi\.realtrackapp\.com/www.${DOMAIN}/g" "/etc/nginx/sites-available/${DOMAIN}"

ln -sf "/etc/nginx/sites-available/${DOMAIN}" "/etc/nginx/sites-enabled/${DOMAIN}"
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable nginx
systemctl reload nginx
ok "Nginx proxying :80 → 127.0.0.1:8080"

# ── 6. TLS (Let's Encrypt) ───────────────────────────────────────────────────
if [[ "$SKIP_SSL" == "1" ]]; then
    warn "SKIP_SSL=1 — using HTTP only. Point DNS to this server and run certbot later."
else
    if [[ -z "$CERTBOT_EMAIL" ]]; then
        warn "CERTBOT_EMAIL not set — skipping SSL. Set it and re-run certbot:"
        echo "  sudo certbot certonly --webroot -w /var/www/certbot -d $DOMAIN -d $WWW_DOMAIN -m you@example.com"
    else
        log "Requesting TLS certificate for $DOMAIN and $WWW_DOMAIN"
        certbot certonly --webroot -w /var/www/certbot \
            -d "$DOMAIN" -d "$WWW_DOMAIN" \
            --email "$CERTBOT_EMAIL" --agree-tos --non-interactive \
            || fail "certbot failed — ensure DNS A records point to this server's public IP"

        cp "$REPO_DIR/infra/nginx/enxi.realtrackapp.com.conf" \
            "/etc/nginx/sites-available/${DOMAIN}"
        sed -i "s/enxi\.realtrackapp\.com/${DOMAIN}/g" "/etc/nginx/sites-available/${DOMAIN}"
        sed -i "s/www\.enxi\.realtrackapp\.com/www.${DOMAIN}/g" "/etc/nginx/sites-available/${DOMAIN}"

        nginx -t
        systemctl reload nginx
        systemctl enable certbot.timer
        systemctl start certbot.timer || true
        ok "HTTPS enabled"
    fi
fi

# ── Summary ──────────────────────────────────────────────────────────────────
ADMIN_PW="$(grep '^ADMIN_PASSWORD=' "$ENV_FILE" | cut -d= -f2- || echo '(see compose/.env)')"
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  EC2 setup complete                                          ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Site:     https://${DOMAIN}"
echo "║  Repo:     ${REPO_DIR}"
echo "║  Admin pw: ${ADMIN_PW}"
echo "║"
echo "║  Redeploy: cd ${REPO_DIR} && bash scripts/redeploy-ec2.sh"
echo "║  Logs:     cd ${REPO_DIR}/compose && docker compose logs -f"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "EC2 security group: allow inbound TCP 22, 80, 443."
echo "DNS: A record ${DOMAIN} (and optional CNAME www) → this instance public IP."
