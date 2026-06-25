#!/bin/bash
# 培翛 peixiao-m5-0624 · 拜访记录 AI 只抽承诺 + 三字段综合抽取 + 可编辑确认保存
# 用法: bash deploy/point-deploy-peixiao-m5-0624.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 培翛 M5-0624 拜访 AI 承诺 → root@${IP}"

ssh "${SSH_OPTS[@]}" "root@${IP}" 'mkdir -p /opt/sandtable/web/js /opt/sandtable/server/routers'

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/visit.html" \
  "root@${IP}:/opt/sandtable/web/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/js/m3-mock-llm.js" \
  "root@${IP}:/opt/sandtable/web/js/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/routers/visits.py" \
  "root@${IP}:/opt/sandtable/server/routers/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/schemas.py" \
  "root@${IP}:/opt/sandtable/server/"

ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
chmod a+rX /opt/sandtable/web/visit.html /opt/sandtable/web/js/m3-mock-llm.js
cd /opt/sandtable/server && source venv/bin/activate && systemctl restart sandtable
sleep 3
systemctl is-active sandtable
REMOTE

echo "==> 外网抽查 visit..."
VISIT_HTML="$(curl -s "http://${IP}/visit.html")"
echo "$VISIT_HTML" | grep -Fq 'AI 抽取承诺' && echo "OK AI 面板标题" || echo "WARN"
echo "$VISIT_HTML" | grep -Fq 'extractCommitmentsFromTopics' && echo "OK m3-mock-llm" || echo "WARN"
echo "$VISIT_HTML" | grep -Fq 'getAIEditedCommitments' && echo "OK 可编辑确认流" || echo "WARN"
echo "$VISIT_HTML" | grep -Fq '确认保存' && echo "OK 两步保存" || echo "WARN"

echo "✅ 完成。验收 http://${IP}/visit.html · 拜访后记录 · Cmd+Shift+R"
