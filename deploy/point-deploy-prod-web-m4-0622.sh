#!/bin/bash
# 定点上云 · prod-web-m4-0622 · M4 全量（只读403/LLM审计/bi_csv月频/五品牌/三包前端）
# 用法: bash deploy/point-deploy-prod-web-m4-0622.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE_WEB="/opt/sandtable/web"
REMOTE_SRV="/opt/sandtable/server"
REMOTE_DB="/opt/sandtable/database"
REMOTE_DATA="/opt/sandtable/data"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 部署目标: root@${IP}"
echo "    标签: prod-web-m4-0622（M4 三包合并）"
echo ""

echo "==> [1/8] 上传 web..."
scp "${SSH_OPTS[@]}" \
  "$ROOT/web/index.html" \
  "$ROOT/web/login.html" \
  "$ROOT/web/profile.html" \
  "$ROOT/web/visit.html" \
  "$ROOT/web/intel.html" \
  "root@${IP}:${REMOTE_WEB}/"
scp "${SSH_OPTS[@]}" \
  "$ROOT/web/js/api-base.js" \
  "$ROOT/web/js/api.js" \
  "$ROOT/web/js/shell.js" \
  "$ROOT/web/js/auth.js" \
  "$ROOT/web/js/visit-common.js" \
  "$ROOT/web/js/m3-config.js" \
  "$ROOT/web/js/m3-mock-llm.js" \
  "root@${IP}:${REMOTE_WEB}/js/"

echo "==> [2/8] 上传 server 核心..."
scp "${SSH_OPTS[@]}" \
  "$ROOT/server/main.py" \
  "$ROOT/server/models.py" \
  "$ROOT/server/schemas.py" \
  "$ROOT/server/config.py" \
  "$ROOT/server/database.py" \
  "$ROOT/server/auth_utils.py" \
  "$ROOT/server/deps_auth.py" \
  "$ROOT/server/llm_service.py" \
  "$ROOT/server/llm_prompts.py" \
  "$ROOT/server/llm_audit.py" \
  "$ROOT/server/bootstrap_local_db.py" \
  "$ROOT/server/dw_sync.py" \
  "$ROOT/server/run_dw_sync.py" \
  "$ROOT/server/seed_m3_auth.py" \
  "$ROOT/server/seed_m4_brands.py" \
  "$ROOT/server/seed_m4_demo_metrics.py" \
  "$ROOT/server/completeness.py" \
  "$ROOT/server/requirements.txt" \
  "root@${IP}:${REMOTE_SRV}/"

echo "==> [3/8] 上传 routers..."
scp "${SSH_OPTS[@]}" \
  "$ROOT/server/routers/auth.py" \
  "$ROOT/server/routers/llm_api.py" \
  "$ROOT/server/routers/dashboard.py" \
  "$ROOT/server/routers/dw.py" \
  "$ROOT/server/routers/profile.py" \
  "$ROOT/server/routers/brands.py" \
  "$ROOT/server/routers/visits.py" \
  "$ROOT/server/routers/intel.py" \
  "root@${IP}:${REMOTE_SRV}/routers/"

echo "==> [4/8] 上传 DB 迁移 + 数仓数据..."
ssh "${SSH_OPTS[@]}" "root@${IP}" "mkdir -p ${REMOTE_DATA}/dw ${REMOTE_DATA}"
scp "${SSH_OPTS[@]}" \
  "$ROOT/database/migrate_m4.sql" \
  "$ROOT/database/migrate_m4_real_brands.sql" \
  "$ROOT/database/migrate_m4_real_brand_content.sql" \
  "$ROOT/database/migrate_m4_metrics_monthly.sql" \
  "root@${IP}:${REMOTE_DB}/"
scp "${SSH_OPTS[@]}" \
  "$ROOT/data/dw/brand_metrics_monthly.csv" \
  "$ROOT/data/dw/bi_mapping.json" \
  "$ROOT/data/dw/bi_mapping.json.example" \
  "$ROOT/data/brands_master.json" \
  "root@${IP}:${REMOTE_DATA}/"
scp "${SSH_OPTS[@]}" \
  "$ROOT/data/dw/brand_metrics_monthly.csv" \
  "$ROOT/data/dw/bi_mapping.json" \
  "$ROOT/data/dw/bi_mapping.json.example" \
  "root@${IP}:${REMOTE_DATA}/dw/"

echo "==> [5/8] 远程 migration + 数仓导入 + 重启..."
ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
APP=/opt/sandtable
ENV="$APP/server/.env"
DB_PASS=$(grep -E '^DB_PASSWORD=' "$ENV" | cut -d= -f2- | tr -d '\r')

ensure_env() {
  local key="$1" val="$2"
  if ! grep -qE "^${key}=" "$ENV" 2>/dev/null; then
    echo "${key}=${val}" >> "$ENV"
    echo "  + ${key}"
  fi
}
ensure_env "DW_METRICS_PERIOD_TYPE" "monthly"
ensure_env "DW_QUALITY_STRICT" "true"

for sql in migrate_m4.sql migrate_m4_real_brands.sql migrate_m4_real_brand_content.sql \
           migrate_m4_metrics_monthly.sql; do
  if [ -f "$APP/database/$sql" ]; then
    mysql -u brand_app -p"${DB_PASS}" brand_sandtable < "$APP/database/$sql" 2>/dev/null || \
      mysql -u brand_app -p"${DB_PASS}" brand_sandtable < "$APP/database/$sql"
    echo "  OK $sql"
  fi
done

cd "$APP/server"
source venv/bin/activate
pip install -q -r requirements.txt
python3 bootstrap_local_db.py
python3 seed_m4_brands.py
python3 run_dw_sync.py "$APP/data/dw/brand_metrics_monthly.csv" --bi
python3 seed_m4_demo_metrics.py

chmod -R a+rX "$APP/web"
systemctl restart sandtable
sleep 5
systemctl is-active sandtable

curl -s http://127.0.0.1:8000/api/brands | python3 -c "
import sys, json
d = json.load(sys.stdin)
keys = [b.get('name_key') for b in d]
print('brands', keys)
assert 'jomoo' in keys, '缺少 jomoo'
"

curl -s http://127.0.0.1:8000/api/dw/latest-period?name_key=hegii | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('hegii latest', d.get('period_value'), 'gmv', d.get('gmv'))
assert d.get('period_value') == '2026-05', d
assert float(d.get('gmv')) == 9885.62
"

curl -s -o /dev/null -w "auth/login HTTP %{http_code}\n" -X POST http://127.0.0.1:8000/api/auth/login \
  -H 'Content-Type: application/json' -d '{"username":"admin","password":"sand123"}'
REMOTE

echo ""
echo "==> [6/8] 外网冒烟 deploy/smoke-test.sh..."
bash "$ROOT/deploy/smoke-test.sh" "http://${IP}"

echo ""
echo "==> [7/8] D-X-M4 smoke（API @ 外网）..."
bash "$ROOT/scripts/dx-m4-smoke.sh" "http://${IP}" || true

echo ""
echo "==> [8/8] 完成"
echo "✅ M4 上云完成。外网硬刷新 Cmd+Shift+R："
echo "   http://${IP}/login.html"
echo "   http://${IP}/profile.html?brand=hegii"
echo "   测试账号: admin/zhou/demo/readonly  密码 sand123"
echo "   标签: prod-web-m4-0622"
echo "   恒洁 2026-05 GMV 应 = 9885.62 万（JD 渠道）"
