#!/bin/bash
# briefing 500 热修：JSON 缓存序列化 + 确保 intel_briefing_cache 表存在
# 用法: bash deploy/point-deploy-fix-briefing-500.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> briefing 500 热修 @ ${IP}"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/routers/intel.py" \
  "root@${IP}:/opt/sandtable/server/routers/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/database/migrate_m2_prod.sql" \
  "root@${IP}:/opt/sandtable/database/"

ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
APP=/opt/sandtable
DB_PASS=$(grep -E '^DB_PASSWORD=' "$APP/server/.env" | cut -d= -f2- | tr -d '\r')

mysql -u brand_app -p"${DB_PASS}" brand_sandtable < "$APP/database/migrate_m2_prod.sql" 2>/dev/null || true

cd "$APP/server"
source venv/bin/activate
pip install -q 'python-multipart>=0.0.6'
systemctl restart sandtable
sleep 3
systemctl is-active sandtable

curl -s -o /dev/null -w "briefing HTTP %{http_code}\n" http://127.0.0.1:8000/api/intel/briefing/midea
REMOTE

echo ""
bash "$ROOT/deploy/smoke-test.sh" "http://${IP}" || true
curl -s -o /dev/null -w "外网 briefing HTTP %{http_code}\n" "http://${IP}/api/intel/briefing/midea"
echo "✅ 应看到 briefing HTTP 200；外网 Cmd+Shift+R 硬刷新 visit/intel"
