#!/bin/bash
# 顶栏 llm状态 链接 + auth.js 缓存刷新
# 用法: bash deploy/point-deploy-auth-llm-link.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 顶栏 llm状态 @ ${IP}"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/js/auth.js" \
  "root@${IP}:/opt/sandtable/web/js/"

for f in index.html profile.html visit.html intel.html login.html change-password.html admin-users.html admin-llm.html; do
  scp "${SSH_OPTS[@]}" "$ROOT/web/$f" "root@${IP}:/opt/sandtable/web/"
done

echo "✅ 完成。硬刷新 http://${IP}/ · 顶栏应为：用户管理 · llm状态 · 修改密码"
echo "   或直接打开 http://${IP}/admin-llm.html"
