#!/bin/bash
# 从已部署的外网地址抓取当前 web 静态页，保存为可回滚快照
# 用法: bash deploy/snapshot-from-cloud.sh [IP] [日期标签]
# 示例: bash deploy/snapshot-from-cloud.sh 117.72.211.51 2026-06-13
set -euo pipefail
IP="${1:-117.72.211.51}"
DATE="${2:-$(date +%Y-%m-%d)}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
SNAP="$REPO/deploy/snapshots/prod-${IP}-${DATE}"
mkdir -p "$SNAP/web/js"
BASE="http://${IP}"
fetch() {
  local path="$1"
  local out="$2"
  echo "  GET ${BASE}${path}"
  curl -sS "${BASE}${path}" -o "$out"
}
echo "==> 快照目录: $SNAP"
fetch "/" "$SNAP/web/index.html"
fetch "/visit.html" "$SNAP/web/visit.html"
fetch "/profile.html" "$SNAP/web/profile.html"
fetch "/intel.html" "$SNAP/web/intel.html"
fetch "/js/shell.js" "$SNAP/web/js/shell.js" || true
fetch "/js/api.js" "$SNAP/web/js/api.js" 2>/dev/null || true
fetch "/js/visit-common.js" "$SNAP/web/js/visit-common.js" 2>/dev/null || true
cat > "$SNAP/README.md" <<EOF
# 生产快照 · ${IP} · ${DATE}

抓取命令: \`bash deploy/snapshot-from-cloud.sh ${IP} ${DATE}\`

回滚: \`bash deploy/snapshots/prod-${IP}-${DATE}/rollback-web.sh ${IP}\`
EOF
cp "$REPO/deploy/snapshots/prod-117.72.211.51-2026-06-13/rollback-web.sh" "$SNAP/rollback-web.sh" 2>/dev/null || \
  cp "$REPO/deploy/snapshots/prod-${IP}-${DATE}/rollback-web.sh" "$SNAP/" 2>/dev/null || true
chmod +x "$SNAP/rollback-web.sh" 2>/dev/null || true
echo "==> 完成。文件列表:"
ls -la "$SNAP/web" "$SNAP/web/js" 2>/dev/null || ls -la "$SNAP/web"
