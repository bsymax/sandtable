#!/bin/bash
# 定点上云 · prod-web-m3-0622 · M3 全量（登录/LLM中台/数仓/三包前端）
# 用法: bash deploy/point-deploy-prod-web-m3-0622.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE_WEB="/opt/sandtable/web"
REMOTE_SRV="/opt/sandtable/server"
REMOTE_DB="/opt/sandtable/database"
REMOTE_DATA="/opt/sandtable/data"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 部署目标: root@${IP}"
echo "    标签: prod-web-m3-0622（M3 全量）"
echo ""

echo "==> [1/7] 上传 web..."
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

echo "==> [2/7] 上传 server 核心..."
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
  "$ROOT/server/bootstrap_local_db.py" \
  "$ROOT/server/dw_sync.py" \
  "$ROOT/server/run_dw_sync.py" \
  "$ROOT/server/seed_m3_auth.py" \
  "$ROOT/server/completeness.py" \
  "$ROOT/server/requirements.txt" \
  "root@${IP}:${REMOTE_SRV}/"

echo "==> [3/7] 上传 routers..."
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

echo "==> [4/7] 上传 DB 迁移 + 数仓 CSV..."
ssh "${SSH_OPTS[@]}" "root@${IP}" "mkdir -p ${REMOTE_DATA}/dw"
scp "${SSH_OPTS[@]}" \
  "$ROOT/database/migrate_m3_auth.sql" \
  "$ROOT/database/migrate_m3_dw.sql" \
  "$ROOT/database/migrate_m3_intel_llm.sql" \
  "root@${IP}:${REMOTE_DB}/"
scp "${SSH_OPTS[@]}" \
  "$ROOT/data/dw/brand_metrics_weekly.csv" \
  "root@${IP}:${REMOTE_DATA}/dw/"

echo "==> [5/7] 远程 migration + 种子 + 重启..."
ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
APP=/opt/sandtable
ENV="$APP/server/.env"
DB_PASS=$(grep -E '^DB_PASSWORD=' "$ENV" | cut -d= -f2- | tr -d '\r')

# M3 环境变量（不覆盖已有项）
ensure_env() {
  local key="$1" val="$2"
  if ! grep -qE "^${key}=" "$ENV" 2>/dev/null; then
    echo "${key}=${val}" >> "$ENV"
    echo "  + ${key}"
  fi
}
ensure_env "LLM_ENABLED" "false"
ensure_env "AUTH_REQUIRED" "false"
ensure_env "SESSION_TTL_HOURS" "72"
if ! grep -qE '^AUTH_SECRET=' "$ENV" 2>/dev/null; then
  echo "AUTH_SECRET=$(openssl rand -hex 24)" >> "$ENV"
  echo "  + AUTH_SECRET (随机)"
fi
ensure_env "AUTH_SALT" "sandtable-auth-salt-prod"

mysql -u brand_app -p"${DB_PASS}" brand_sandtable < "$APP/database/migrate_m3_auth.sql"
mysql -u brand_app -p"${DB_PASS}" brand_sandtable < "$APP/database/migrate_m3_dw.sql" 2>/dev/null || true

cd "$APP/server"
source venv/bin/activate
pip install -q -r requirements.txt
python3 bootstrap_local_db.py
python3 seed_m3_auth.py
python3 run_dw_sync.py "$APP/data/dw/brand_metrics_weekly.csv" 2>/dev/null || echo "  WARN: dw_sync 跳过（可后续手动跑）"

chmod -R a+rX "$APP/web"
systemctl restart sandtable
sleep 4
systemctl is-active sandtable

curl -s -o /dev/null -w "brands HTTP %{http_code}\n" http://127.0.0.1:8000/api/brands
curl -s -o /dev/null -w "auth/login HTTP %{http_code}\n" -X POST http://127.0.0.1:8000/api/auth/login \
  -H 'Content-Type: application/json' -d '{"username":"admin","password":"sand123"}'
curl -s -o /dev/null -w "llm/status HTTP %{http_code}\n" http://127.0.0.1:8000/api/llm/status
curl -s -o /dev/null -w "dashboard HTTP %{http_code}\n" http://127.0.0.1:8000/api/dashboard/summary-line
REMOTE

echo ""
echo "==> [6/7] 外网冒烟 deploy/smoke-test.sh..."
bash "$ROOT/deploy/smoke-test.sh" "http://${IP}"

echo ""
echo "==> [7/7] D-X-M3 smoke（API @ 外网）..."
STATIC_BASE="http://${IP}" bash "$ROOT/scripts/dx-m3-smoke.sh" "http://${IP}" || true

echo ""
echo "✅ M3 上云完成。外网硬刷新 Cmd+Shift+R："
echo "   http://${IP}/login.html      （M3 登录）"
echo "   http://${IP}/                （工作台）"
echo "   http://${IP}/profile.html    （档案 AI Tab）"
echo "   http://${IP}/visit.html      （拜访 AI 面板）"
echo "   http://${IP}/intel.html      （情报 AI 简报）"
echo "   测试账号: admin/zhou/demo/readonly  密码 sand123"
echo "   标签: prod-web-m3-0622"
