#!/bin/bash
# 热修 · 历史互动/承诺追踪旧厨电 demo 文案 → 五卫浴品牌
set -euo pipefail

IP="${DEPLOY_IP:-117.72.211.51}"
SSH_OPTS=(-o ConnectTimeout=30)

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SQL="$ROOT/database/migrate_m4_visit_brand_content.sql"

echo ">>> 上传 SQL ..."
scp "${SSH_OPTS[@]}" "$SQL" "root@${IP}:/opt/sandtable/database/migrate_m4_visit_brand_content.sql"

echo ">>> 远程执行迁移（brand_app + server/.env 密码）..."
ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
APP=/opt/sandtable
DB_PASS=$(grep -E '^DB_PASSWORD=' "$APP/server/.env" | cut -d= -f2- | tr -d '\r')
if [ -z "$DB_PASS" ]; then
  echo "ERROR: 未读到 $APP/server/.env 中的 DB_PASSWORD"
  exit 1
fi

mysql -u brand_app -p"${DB_PASS}" brand_sandtable < "$APP/database/migrate_m4_visit_brand_content.sql"

echo ">>> 抽样验证 visits.purpose (brand_id=1) ..."
mysql -u brand_app -p"${DB_PASS}" brand_sandtable -N -e \
  "SELECT id, LEFT(purpose,60) FROM visits WHERE brand_id=1 ORDER BY id LIMIT 5;"

echo ">>> 抽样验证 commitments ..."
mysql -u brand_app -p"${DB_PASS}" brand_sandtable -N -e \
  "SELECT id, content FROM commitments ORDER BY id LIMIT 6;"
REMOTE

echo "✅ 外网硬刷新 profile.html?brand=jomoo → 历史互动 / 承诺追踪应无「美的/空气炸锅」等旧文案"
