#!/bin/bash
# J-7 / briefing：intel 热修 + 可选恢复美的 P0（Tab3 验收）
# 用法: bash deploy/point-deploy-intel-briefing-tab3.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> intel briefing + Tab3 数据 @ ${IP}"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/routers/intel.py" \
  "root@${IP}:/opt/sandtable/server/routers/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/database/fix_midea_p0_tab3.sql" \
  "root@${IP}:/opt/sandtable/database/"

ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
APP=/opt/sandtable
DB_PASS=$(grep -E '^DB_PASSWORD=' "$APP/server/.env" | cut -d= -f2- | tr -d '\r')

cd "$APP/server"
source venv/bin/activate
pip install -q 'python-multipart>=0.0.6'
systemctl restart sandtable
sleep 3

mysql -u brand_app -p"${DB_PASS}" brand_sandtable < "$APP/database/fix_midea_p0_tab3.sql"

curl -s -o /dev/null -w "briefing midea HTTP %{http_code}\n" http://127.0.0.1:8000/api/intel/briefing/midea
curl -s http://127.0.0.1:8000/api/intel/briefing/midea | python3 -c "
import json,sys
d=json.load(sys.stdin)
p0=[a for a in d.get('active_alerts',[]) if a.get('priority')=='P0']
print('active_p0', len(p0))
for a in p0[:3]:
    print(' ', a.get('category'), a.get('title','')[:40])
"
REMOTE

echo ""
echo "✅ 验收："
echo "   curl http://${IP}/api/intel/briefing/midea  → 200，active P0 ≥ 2"
echo "   http://${IP}/profile.html 美的 Tab3 左右栏应有数据"
