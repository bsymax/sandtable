#!/bin/bash
# 培翛 peixiao-m6-0630 · 历史拜访导入 + mock 过滤 + 工具包页
# 用法: bash deploy/point-deploy-peixiao-m6-0630.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 培翛 M6-0630 → root@${IP}"

ssh "${SSH_OPTS[@]}" "root@${IP}" 'mkdir -p /opt/sandtable/web/js /opt/sandtable/web/toolkit /opt/sandtable/server/routers /opt/sandtable/docs/templates'

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/visit.html" \
  "root@${IP}:/opt/sandtable/web/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/js/shell.js" \
  "root@${IP}:/opt/sandtable/web/js/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/toolkit/talking-points.html" \
  "$ROOT/web/toolkit/brand-report.html" \
  "root@${IP}:/opt/sandtable/web/toolkit/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/docs/templates/visit-history-import-template.csv" \
  "$ROOT/docs/templates/visit-history-import-readme.md" \
  "root@${IP}:/opt/sandtable/docs/templates/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/schemas.py" \
  "root@${IP}:/opt/sandtable/server/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/routers/visits.py" \
  "root@${IP}:/opt/sandtable/server/routers/"

ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
chmod -R a+rX /opt/sandtable/web/visit.html /opt/sandtable/web/js/shell.js /opt/sandtable/web/toolkit /opt/sandtable/docs/templates
cd /opt/sandtable/server && source venv/bin/activate && systemctl restart sandtable
sleep 3
systemctl is-active sandtable
REMOTE

echo "==> 外网抽查..."
VISIT="$(curl -s "http://${IP}/visit.html")"
echo "$VISIT" | grep -Fq 'import-history' && echo "OK import-history 前端" || echo "WARN"
echo "$VISIT" | grep -Fq '历史导入' && echo "OK 历史导入 Tab" || echo "WARN"
echo "$VISIT" | grep -Fq '厨小事业部' && echo "WARN: 仍有厨小" || echo "OK 无厨小"
curl -sf -o /dev/null "http://${IP}/toolkit/talking-points.html" && echo "OK 谈参页" || echo "WARN 谈参页"
curl -sf -o /dev/null "http://${IP}/toolkit/brand-report.html" && echo "OK 品牌报告页" || echo "WARN 品牌报告页"

echo "✅ 完成。验收 http://${IP}/visit.html · 历史导入 · http://${IP}/toolkit/talking-points.html"
