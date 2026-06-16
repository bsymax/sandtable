#!/bin/bash
# 定点上云 · prod-web-2026-06-18 · M2 三包合并（佳璇/培翛/开开）
# 用法: bash deploy/point-deploy-prod-web-2026-06-18.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE_WEB="/opt/sandtable/web"
REMOTE_SRV="/opt/sandtable/server"
REMOTE_DB="/opt/sandtable/database"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 部署目标: root@${IP}"
echo "    标签: prod-web-2026-06-18（M2 三包合并）"
echo ""

echo "==> [1/5] 上传 web..."
scp "${SSH_OPTS[@]}" \
  "$ROOT/web/profile.html" \
  "$ROOT/web/visit.html" \
  "$ROOT/web/intel.html" \
  "root@${IP}:${REMOTE_WEB}/"
scp "${SSH_OPTS[@]}" \
  "$ROOT/web/js/visit-common.js" \
  "root@${IP}:${REMOTE_WEB}/js/"

echo "==> [2/5] 上传 server..."
scp "${SSH_OPTS[@]}" \
  "$ROOT/server/models.py" \
  "$ROOT/server/schemas.py" \
  "root@${IP}:${REMOTE_SRV}/"
scp "${SSH_OPTS[@]}" \
  "$ROOT/server/routers/profile.py" \
  "$ROOT/server/routers/brands.py" \
  "$ROOT/server/routers/intel.py" \
  "$ROOT/server/routers/visits.py" \
  "root@${IP}:${REMOTE_SRV}/routers/"

echo "==> [3/5] 上传 DB 迁移..."
scp "${SSH_OPTS[@]}" \
  "$ROOT/database/migrate_m2_prod.sql" \
  "root@${IP}:${REMOTE_DB}/"

echo "==> [4/5] 远程 migration + 重启..."
ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
APP=/opt/sandtable
DB_PASS=$(grep -E '^DB_PASSWORD=' "$APP/server/.env" | cut -d= -f2- | tr -d '\r')

mysql -u brand_app -p"${DB_PASS}" brand_sandtable < "$APP/database/migrate_m2_prod.sql" 2>/dev/null || true

cd "$APP/server"
source venv/bin/activate
pip install -q 'python-multipart>=0.0.6'

chmod -R a+rX "$APP/web"
systemctl restart sandtable
sleep 3
systemctl is-active sandtable
curl -s -o /dev/null -w "brands HTTP %{http_code}\n" http://127.0.0.1:8000/api/brands
curl -s -o /dev/null -w "briefing HTTP %{http_code}\n" http://127.0.0.1:8000/api/intel/briefing/midea
curl -s -o /dev/null -w "csv-template HTTP %{http_code}\n" http://127.0.0.1:8000/api/intel/news/csv/template
REMOTE

echo ""
echo "==> [5/5] 外网冒烟..."
bash "$ROOT/deploy/smoke-test.sh" "http://${IP}" || true
echo ""
echo "✅ 完成。外网硬刷新 Cmd+Shift+R："
echo "   http://${IP}/profile.html  （Tab1 规则段 / Tab2 竞争机会）"
echo "   http://${IP}/visit.html   （提醒接承诺+briefing）"
echo "   http://${IP}/intel.html   （CSV / 分页 / 模板）"
