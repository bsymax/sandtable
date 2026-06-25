#!/bin/bash
# 九牧 Tab2 loading 占位污染修复 · llm_prompts + profile + 清库
# 用法: bash deploy/point-deploy-jomoo-strategy-fix.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 九牧竞争/机会 Tab2 修复 @ ${IP}"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/llm_prompts.py" \
  "root@${IP}:/opt/sandtable/server/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/routers/profile.py" \
  "root@${IP}:/opt/sandtable/server/routers/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/profile.html" \
  "root@${IP}:/opt/sandtable/web/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/database/fix_jomoo_strategy_loading.sql" \
  "root@${IP}:/opt/sandtable/database/"

ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
APP=/opt/sandtable
DB_PASS=$(grep -E '^DB_PASSWORD=' "$APP/server/.env" | cut -d= -f2- | tr -d '\r')

cd "$APP/server"
source venv/bin/activate
systemctl restart sandtable
sleep 3

mysql -u brand_app -p"${DB_PASS}" brand_sandtable < "$APP/database/fix_jomoo_strategy_loading.sql"

echo "==> jomoo profile fields"
mysql -u brand_app -p"${DB_PASS}" brand_sandtable -N -e "
SELECT IFNULL(competitive_landscape,'(null)'), IFNULL(growth_opportunities,'(null)')
FROM brand_profiles bp JOIN brands b ON b.id=bp.brand_id WHERE b.name_key='jomoo';"

echo "==> strategy API fallback"
curl -s -X POST "http://127.0.0.1:8000/api/brands/profile/jomoo/ai/strategy" \
  -H "Content-Type: application/json" -d '{}' | python3 -c "
import json,sys
d=json.load(sys.stdin)
c=(d.get('competitive_landscape') or '')[:80]
o=(d.get('growth_opportunities') or '')[:80]
print('source', d.get('source'))
print('comp', c)
print('opp', o)
print('loading', '正在生成' in (d.get('competitive_landscape') or ''))
"
REMOTE

echo ""
echo "✅ 验收 http://${IP}/profile.html?brand=jomoo · Tab2 竞争与机会 · Cmd+Shift+R"
