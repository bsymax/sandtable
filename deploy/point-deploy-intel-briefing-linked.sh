#!/bin/bash
# briefing 活跃预警口径对齐 profile：status != closed（含 linked）
# 用法: bash deploy/point-deploy-intel-briefing-linked.sh [IP] [brand_key]
set -euo pipefail
IP="${1:-117.72.211.51}"
BRAND_KEY="${2:-jomoo}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> intel briefing 口径热修 @ ${IP} · 验收品牌 ${BRAND_KEY}"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/routers/intel.py" \
  "root@${IP}:/opt/sandtable/server/routers/"

ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s "$BRAND_KEY" <<'REMOTE'
set -euo pipefail
BRAND_KEY="$1"
APP=/opt/sandtable
DB_PASS=$(grep -E '^DB_PASSWORD=' "$APP/server/.env" | cut -d= -f2- | tr -d '\r')

cd "$APP/server"
source venv/bin/activate
systemctl restart sandtable
sleep 3

mysql -u brand_app -p"${DB_PASS}" brand_sandtable -e "DELETE FROM intel_briefing_cache;"

curl -s -o /dev/null -w "briefing ${BRAND_KEY} HTTP %{http_code}\n" "http://127.0.0.1:8000/api/intel/briefing/${BRAND_KEY}"
curl -s "http://127.0.0.1:8000/api/intel/briefing/${BRAND_KEY}" | python3 -c "
import json,sys
d=json.load(sys.stdin)
p0=[a for a in d.get('active_alerts',[]) if a.get('priority')=='P0' and a.get('status')!='closed']
linked=[a for a in p0 if a.get('status')=='linked']
print('active_p0', len(p0), 'linked_p0', len(linked), 'stats', d.get('stats',{}))
for a in p0[:5]:
    print(' ', a.get('status'), a.get('category'), (a.get('title') or '')[:48])
"
REMOTE

echo ""
echo "✅ 验收："
echo "   curl http://${IP}/api/intel/briefing/${BRAND_KEY}  → active_alerts 含 linked"
echo "   http://${IP}/profile.html?brand=${BRAND_KEY} Tab3 P0 条数 = 情报页未关闭 P0"
