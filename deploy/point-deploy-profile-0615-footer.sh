#!/bin/bash
# 单文件上云 · profile.html（历史互动 Tab 底部仅保留「安排拜访」）
# 用法: bash deploy/point-deploy-profile-0615-footer.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 上传 profile.html → root@${IP}:/opt/sandtable/web/"
scp "${SSH_OPTS[@]}" "$ROOT/web/profile.html" "root@${IP}:/opt/sandtable/web/profile.html"
ssh "${SSH_OPTS[@]}" "root@${IP}" 'chmod a+rX /opt/sandtable/web/profile.html'
echo "✅ 完成。硬刷新 http://${IP}/profile.html → 历史互动 Tab 底部应只有「安排拜访」"
