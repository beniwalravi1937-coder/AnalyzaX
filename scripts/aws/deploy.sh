#!/usr/bin/env bash
# ==============================================================================
# AnalyzaX — Deploy the committed code (git HEAD) to the EC2 host
#
#   1. Packs HEAD with `git archive` (only committed files; no .env, data or venv)
#   2. Uploads and unpacks it into /opt/analyzax on the host
#   3. On first deploy, creates /opt/analyzax/.env from .env.production.example
#      with freshly generated secrets (generated on the host, never printed)
#   4. Builds and starts docker-compose.prod.yml, then checks /health/live and /
#
# Usage:  scripts/aws/deploy.sh            (reads scripts/aws/.instance)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/.instance"

SSH_OPTS=(-i "$KEY_FILE" -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30)
HOST="ubuntu@${PUBLIC_IP}"
SHA=$(git -C "$REPO_ROOT" rev-parse --short HEAD)
ARCHIVE="$(mktemp -d)/analyzax-${SHA}.tar.gz"

echo "==> Waiting for host bootstrap on $PUBLIC_IP"
for _ in $(seq 1 60); do
  ssh "${SSH_OPTS[@]}" -o ConnectTimeout=5 "$HOST" 'test -f /var/lib/analyzax-bootstrap-done' 2>/dev/null && break
  sleep 10
done
ssh "${SSH_OPTS[@]}" "$HOST" 'test -f /var/lib/analyzax-bootstrap-done' \
  || { echo "ERROR: host bootstrap not finished (see /var/log/cloud-init-output.log)" >&2; exit 1; }

echo "==> Packing commit $SHA"
git -C "$REPO_ROOT" archive --format=tar.gz -o "$ARCHIVE" HEAD

echo "==> Uploading"
scp "${SSH_OPTS[@]}" "$ARCHIVE" "$HOST:/tmp/analyzax.tar.gz"

echo "==> Building and starting containers (first build takes several minutes)"
ssh "${SSH_OPTS[@]}" "$HOST" PUBLIC_IP="$PUBLIC_IP" SHA="$SHA" 'bash -s' <<'REMOTE'
set -euo pipefail
cd /opt/analyzax
tar -xzf /tmp/analyzax.tar.gz
rm -f /tmp/analyzax.tar.gz

if [ ! -f .env ]; then
  echo "==> Creating .env with generated secrets"
  cp .env.production.example .env
  chmod 600 .env
  DB_PASS=$(openssl rand -hex 24)
  sed -i \
    -e "s#^SECRET_KEY=.*#SECRET_KEY=\"$(openssl rand -hex 32)\"#" \
    -e "s#^AUTH_SESSION_SECRET=.*#AUTH_SESSION_SECRET=\"$(openssl rand -hex 32)\"#" \
    -e "s#REPLACE_WITH_STRONG_PRODUCTION_DB_PASSWORD#${DB_PASS}#g" \
    -e "s#^ALLOWED_CORS_ORIGINS=.*#ALLOWED_CORS_ORIGINS=[\"http://${PUBLIC_IP}\"]#" \
    -e "s#^SECURE_COOKIES=.*#SECURE_COOKIES=false#" \
    -e "s#^BILLING_ENABLED=.*#BILLING_ENABLED=false#" \
    -e "s#^BILLING_SECRET_KEY=.*#BILLING_SECRET_KEY=\"\"#" \
    -e "s#^BILLING_PORTAL_RETURN_URL=.*#BILLING_PORTAL_RETURN_URL=\"http://${PUBLIC_IP}/settings/billing\"#" \
    -e "s#^AI_PROVIDER=.*#AI_PROVIDER=gemini#" \
    -e "s#^AI_API_KEY=.*#AI_API_KEY=\"\"#" \
    .env
  grep -q '^GEMINI_API_KEY=' .env || printf 'GEMINI_API_KEY=""\nGEMINI_MODEL="gemini-2.5-flash"\n' >> .env
fi
sed -i "s#^RELEASE_COMMIT_SHA=.*#RELEASE_COMMIT_SHA=\"${SHA}\"#" .env

docker compose -f docker-compose.prod.yml up -d --build --remove-orphans
# nginx resolves upstream container IPs only at startup; recreated containers
# get new IPs, so restart the edge proxy to avoid 502s
docker compose -f docker-compose.prod.yml restart proxy
docker image prune -f >/dev/null

echo "==> Waiting for backend and frontend health"
for _ in $(seq 1 30); do
  if curl -fsS http://127.0.0.1/health/live >/dev/null 2>&1 && curl -fsS http://127.0.0.1/ >/dev/null 2>&1; then
    echo "==> Backend and frontend healthy"; docker compose -f docker-compose.prod.yml ps; exit 0
  fi
  sleep 5
done
echo "ERROR: backend or frontend did not become healthy" >&2
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs --tail=60 backend
exit 1
REMOTE

echo "==> Deployed $SHA -> http://${PUBLIC_IP}"
