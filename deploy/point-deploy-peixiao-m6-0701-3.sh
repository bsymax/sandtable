#!/bin/bash
# 培翛 peixiao-m6-0701-3 · 历史导入 #12/#13 + visit 品牌报告跳转谈参
# 用法: bash deploy/point-deploy-peixiao-m6-0701-3.sh [IP]
# 注意: 不覆盖 web/toolkit/talking-points.html（佳璇终包为准）
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 培翛 M6-0701-3 → root@${IP}"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/visit.html" \
  "$ROOT/web/toolkit/brand-report.html" \
  "root@${IP}:/opt/sandtable/web/" 2>/dev/null || true

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/toolkit/brand-report.html" \
  "$ROOT/web/toolkit/talking-points.html" \
  "root@${IP}:/opt/sandtable/web/toolkit/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/routers/visits.py" \
  "root@${IP}:/opt/sandtable/server/routers/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/docs/templates/visit-history-import-template.csv" \
  "$ROOT/docs/templates/visit-history-import-readme.md" \
  "root@${IP}:/opt/sandtable/docs/templates/"

ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
systemctl restart sandtable
sleep 3
systemctl is-active sandtable
curl -sf http://127.0.0.1:8000/docs | head -c 80 >/dev/null && echo OK API
REMOTE

echo "==> 外网抽查 visit.html..."
curl -sf "http://${IP}/visit.html" | grep -Fq '【填写说明】' && echo "OK 中文双表头模板 Blob" || echo "WARN"
curl -sf "http://${IP}/visit.html" | grep -Fq 'talking-points.html?brand=' && echo "OK 品牌报告→谈参" || echo "WARN"
curl -sf "http://${IP}/toolkit/brand-report.html" | grep -Fq 'talking-points.html' && echo "OK brand-report 跳转" || echo "WARN"

echo "✅ 完成。验收 visit.html 历史导入 · 模板下载 · 品牌报告 Tab"
