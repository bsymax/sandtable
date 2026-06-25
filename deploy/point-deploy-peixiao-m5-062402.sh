#!/bin/bash
# 培翛 peixiao-m5-062402 · AI 承诺 deadline 结构化入库（截止日期分离）
# 用法: bash deploy/point-deploy-peixiao-m5-062402.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 培翛 M5-062402 截止日期分离 → root@${IP}"

ssh "${SSH_OPTS[@]}" "root@${IP}" 'mkdir -p /opt/sandtable/web/js /opt/sandtable/server/routers'

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/visit.html" \
  "root@${IP}:/opt/sandtable/web/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/js/m3-mock-llm.js" \
  "root@${IP}:/opt/sandtable/web/js/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/schemas.py" \
  "root@${IP}:/opt/sandtable/server/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/routers/visits.py" \
  "root@${IP}:/opt/sandtable/server/routers/"

ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
chmod a+rX /opt/sandtable/web/visit.html /opt/sandtable/web/js/m3-mock-llm.js
cd /opt/sandtable/server && source venv/bin/activate && systemctl restart sandtable
sleep 3
systemctl is-active sandtable
REMOTE

echo "==> 外网抽查 visit.html..."
VISIT="$(curl -s "http://${IP}/visit.html")"
echo "$VISIT" | grep -Fq 'ai_commitments' && echo "OK payload.ai_commitments" || echo "WARN"
echo "$VISIT" | grep -Fq 'syncCommitmentDeadlines' && echo "WARN: 仍有旧同步函数" || echo "OK 已删 syncCommitmentDeadlines"

echo "✅ 完成。验收 http://${IP}/visit.html · 保存记录后承诺跟踪「截止」列应显示 AI 抽取日期"
