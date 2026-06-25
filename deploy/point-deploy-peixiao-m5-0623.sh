#!/bin/bash
# 培翛 peixiao-m5-0623 · 承诺行内编辑 + Max API 扩容
# 用法: bash deploy/point-deploy-peixiao-m5-0623.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 培翛 M5-0623 承诺编辑 + API → root@${IP}"

ssh "${SSH_OPTS[@]}" "root@${IP}" 'mkdir -p /opt/sandtable/web/js /opt/sandtable/server/routers'

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/visit.html" \
  "root@${IP}:/opt/sandtable/web/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/js/visit-common.js" \
  "root@${IP}:/opt/sandtable/web/js/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/routers/visits.py" \
  "root@${IP}:/opt/sandtable/server/routers/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/schemas.py" \
  "root@${IP}:/opt/sandtable/server/"

ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
chmod a+rX /opt/sandtable/web/visit.html /opt/sandtable/web/js/visit-common.js
cd /opt/sandtable/server && source venv/bin/activate && systemctl restart sandtable
sleep 3
systemctl is-active sandtable
REMOTE

echo "==> 外网抽查 visit..."
VISIT_HTML="$(curl -s "http://${IP}/visit.html")"
echo "$VISIT_HTML" | grep -Fq '可直接编辑' && echo "OK 承诺跟踪 tag" || echo "WARN: tag"
echo "$VISIT_HTML" | grep -Fq 'saveCommitmentField' && echo "OK saveCommitmentField" || echo "WARN: JS"
echo "$VISIT_HTML" | grep -Fq 'data-field=\"content\"' && echo "OK 内联 content input" || echo "WARN: renderCommitmentsTable"

echo "✅ 完成。验收 http://${IP}/visit.html?vtab=commitments · Cmd+Shift+R"
