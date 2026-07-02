#!/bin/bash
# 佳璇 jiaxuan-m6-0702 · 谈参 PDF 本地化 html2pdf（不依赖 CDN）
# 用法: bash deploy/point-deploy-jiaxuan-m6-0702.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE_WEB="/opt/sandtable/web"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 佳璇 M6-0702 谈参 PDF 本地化 → root@${IP}"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/js/html2pdf.bundle.min.js" \
  "root@${IP}:${REMOTE_WEB}/js/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/toolkit/talking-points.html" \
  "root@${IP}:${REMOTE_WEB}/toolkit/"

ssh "${SSH_OPTS[@]}" "root@${IP}" "chmod -R a+rX ${REMOTE_WEB}/js ${REMOTE_WEB}/toolkit"

echo "==> 外网抽查..."
TP="$(curl -s "http://${IP}/toolkit/talking-points.html")"
echo "$TP" | grep -Fq '../js/html2pdf.bundle.min.js' && echo "OK 本地 html2pdf 引用" || echo "WARN 仍引用 CDN"
curl -sf "http://${IP}/js/html2pdf.bundle.min.js" | head -c 80 | grep -Fq 'html2pdf' && echo "OK html2pdf 静态可访问" || echo "WARN js 404"

echo "✅ 完成。验收 http://${IP}/toolkit/talking-points.html → 预览 → 下载 PDF"
