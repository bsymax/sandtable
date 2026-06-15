#!/bin/bash
# 三模块顶栏统一 · shell.js + 三页 HTML
# 用法: bash deploy/point-deploy-topbar-0615.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 上传顶栏统一包 → root@${IP}"
scp "${SSH_OPTS[@]}" \
  "$ROOT/web/js/shell.js" \
  "root@${IP}:/opt/sandtable/web/js/shell.js"
scp "${SSH_OPTS[@]}" \
  "$ROOT/web/profile.html" \
  "$ROOT/web/visit.html" \
  "$ROOT/web/intel.html" \
  "root@${IP}:/opt/sandtable/web/"
ssh "${SSH_OPTS[@]}" "root@${IP}" 'chmod -R a+rX /opt/sandtable/web'
echo "✅ 完成。三模块 Cmd+Shift+R 后顶栏应一致："
echo "   ← 工作台 › 品牌沙盘 M1 › （档案/拜访/情报）"
