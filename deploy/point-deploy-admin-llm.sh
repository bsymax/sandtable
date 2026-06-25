#!/bin/bash
# admin LLM 状态页 + 诊断 API
# 用法: bash deploy/point-deploy-admin-llm.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> admin LLM 诊断页 @ ${IP}"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/llm_diagnostics.py" \
  "$ROOT/server/schemas.py" \
  "root@${IP}:/opt/sandtable/server/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/routers/llm_api.py" \
  "root@${IP}:/opt/sandtable/server/routers/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/admin-llm.html" \
  "root@${IP}:/opt/sandtable/web/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/js/auth.js" \
  "root@${IP}:/opt/sandtable/web/js/"

ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
cd /opt/sandtable/server
source venv/bin/activate
systemctl restart sandtable
sleep 3
systemctl is-active sandtable
curl -s http://127.0.0.1:8000/api/llm/status
echo ""
REMOTE

echo ""
echo "✅ admin 登录后打开 http://${IP}/admin-llm.html · 点「网关探活」"
echo "   启用真 LLM：bash deploy/point-config-llm-cloud.sh（本机 server/.env 填好 Key）"
