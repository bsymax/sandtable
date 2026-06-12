#!/bin/bash
# 定点上云 · prod-web-2026-06-13-2（S5 工作台 + api-base + 待办品牌字段）
# 用法: bash deploy/point-deploy-prod-web-2026-06-13-2.sh [IP]
# 会提示 root SSH 密码（2～3 次）
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE_WEB="/opt/sandtable/web"
REMOTE_SRV="/opt/sandtable/server"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 部署目标: root@${IP}"
echo "    标签: prod-web-2026-06-13-2（区别于 prod-web-2026-06-13）"
echo ""

echo "==> [1/3] 上传 web 静态页..."
scp "${SSH_OPTS[@]}" \
  "$ROOT/web/index.html" \
  "$ROOT/web/profile.html" \
  "$ROOT/web/visit.html" \
  "$ROOT/web/intel.html" \
  "root@${IP}:${REMOTE_WEB}/"
scp "${SSH_OPTS[@]}" \
  "$ROOT/web/js/api-base.js" \
  "$ROOT/web/js/api.js" \
  "$ROOT/web/js/shell.js" \
  "$ROOT/web/js/visit-common.js" \
  "root@${IP}:${REMOTE_WEB}/js/"

echo "==> [2/3] 上传 server 补丁..."
scp "${SSH_OPTS[@]}" \
  "$ROOT/server/schemas.py" \
  "root@${IP}:${REMOTE_SRV}/schemas.py"
scp "${SSH_OPTS[@]}" \
  "$ROOT/server/routers/visits.py" \
  "root@${IP}:${REMOTE_SRV}/routers/visits.py"

echo "==> [3/3] 重启后端 + 权限..."
ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
chmod -R a+rX /opt/sandtable/web
systemctl restart sandtable
sleep 2
systemctl is-active sandtable
curl -s -o /dev/null -w "brands HTTP %{http_code}\n" http://127.0.0.1:8000/api/brands
REMOTE

echo ""
echo "==> 外网冒烟..."
bash "$ROOT/deploy/smoke-test.sh" "http://${IP}" || true
echo ""
echo "✅ 完成。请外网 Cmd+Shift+R 硬刷新："
echo "   http://${IP}/"
echo "   http://${IP}/profile.html"
echo "   http://${IP}/visit.html"
echo "   http://${IP}/intel.html"
