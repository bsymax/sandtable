#!/bin/bash
# 回滚到 prod-web-2026-06-13-2 快照（仅 web 静态页，不动 server/数据库）
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
WEB="$ROOT/web"
REMOTE="/opt/sandtable/web"
if [[ ! -f "$WEB/index.html" ]]; then
  echo "错误：找不到 $WEB/index.html"
  exit 1
fi
echo "==> 回滚 prod-web-2026-06-13-2 → root@${IP}:${REMOTE}/"
scp "$WEB/index.html" "root@${IP}:${REMOTE}/index.html"
for f in visit.html profile.html intel.html; do
  [[ -f "$WEB/$f" ]] && scp "$WEB/$f" "root@${IP}:${REMOTE}/$f"
done
for f in api-base.js shell.js api.js visit-common.js; do
  [[ -f "$WEB/js/$f" ]] && scp "$WEB/js/$f" "root@${IP}:${REMOTE}/js/$f"
done
echo "==> 完成。请外网硬刷新： http://${IP}/"
