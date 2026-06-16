#!/bin/bash
# 佳璇 M2 补丁 jiaxuan-m2-patch-0618 / 0618-b / 0618-c
# 0618-b：Tab4 承诺按品牌 visit_id 筛选
# 0618-c：Tab4 拜访日历改用 VisitCommon 同表 + web/js/visit-common.js
# 可选一并上 intel briefing 热修（若尚未部署）
# 用法: bash deploy/point-deploy-jiaxuan-patch-0618.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 佳璇补丁 0618 @ ${IP}"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/profile.html" \
  "root@${IP}:/opt/sandtable/web/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/js/visit-common.js" \
  "root@${IP}:/opt/sandtable/web/js/"

# briefing 500 热修（已合并过可跳过，重复执行无害）
scp "${SSH_OPTS[@]}" \
  "$ROOT/server/routers/intel.py" \
  "root@${IP}:/opt/sandtable/server/routers/" 2>/dev/null || true

ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
APP=/opt/sandtable
chmod -R a+rX "$APP/web"
systemctl restart sandtable
sleep 2
curl -s -o /dev/null -w "profile static OK (skip body)\n"
curl -s -o /dev/null -w "briefing HTTP %{http_code}\n" http://127.0.0.1:8000/api/intel/briefing/midea
REMOTE

echo ""
echo "✅ 外网验收："
echo "   http://${IP}/profile.html  Tab2 / Tab4（J-8、D-J-1）"
echo "   硬刷新 Cmd+Shift+R"
