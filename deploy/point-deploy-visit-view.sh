#!/bin/bash
# 定点上云 · 拜访「查看」只读记录（visit.html + visit-common.js + profile.html）
# 用法: bash deploy/point-deploy-visit-view.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE_WEB="/opt/sandtable/web"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 部署目标: root@${IP}"
echo "    标签: visit-view（已完成拜访 → 拜访后记录只读）"
echo ""

echo "==> 上传 web/visit.html web/profile.html web/js/visit-common.js ..."
tar czf - -C "$ROOT" web/visit.html web/profile.html web/js/visit-common.js \
  | ssh "${SSH_OPTS[@]}" "root@${IP}" "tar xzf - -C ${REMOTE_WEB%/*} && chmod -R a+rX ${REMOTE_WEB}"

echo ""
echo "==> 验收（外网应含 viewVisitRecord，不应含 详情（演示））"
curl -s --max-time 10 "http://${IP}/js/visit-common.js?v=20260618-visit-view-b" \
  | rg -n "viewVisitRecord|详情（演示）" || true
curl -s --max-time 10 "http://${IP}/visit.html" \
  | rg -n "visit-common.js|record-view-banner" || true

echo ""
echo "==> 完成。浏览器请 Cmd+Shift+R 硬刷新 visit.html / profile.html"
