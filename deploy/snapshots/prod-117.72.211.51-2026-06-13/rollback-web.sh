#!/bin/bash
# 将本快照中的 web/ 文件恢复到京东云（仅静态页，不动数据库与 server）
# 注意：Nginx 根目录对应 /opt/sandtable/web/，URL 为 /index.html 即 web/index.html
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
WEB="$ROOT/web"
REMOTE="/opt/sandtable/web"
if [[ ! -f "$WEB/index.html" ]]; then
  echo "错误：找不到 $WEB/index.html"
  exit 1
fi
echo "==> 回滚到 root@${IP}:${REMOTE}/"
scp "$WEB/index.html" "root@${IP}:${REMOTE}/index.html"
for f in visit.html profile.html intel.html; do
  [[ -f "$WEB/$f" ]] && scp "$WEB/$f" "root@${IP}:${REMOTE}/$f"
done
for f in shell.js api.js visit-common.js; do
  [[ -f "$WEB/js/$f" ]] && scp "$WEB/js/$f" "root@${IP}:${REMOTE}/js/$f"
done
echo "==> 完成。请外网硬刷新验证： http://${IP}/"
