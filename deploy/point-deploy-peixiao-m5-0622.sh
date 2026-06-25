#!/bin/bash
# 培翛 M5 peixiao-m5-pilot / pilot-2 / pilot-3 · visit + docs（不含 shell/auth/index）
# 用法: bash deploy/point-deploy-peixiao-m5-0622.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 培翛 M5 合并上云 → root@${IP}"

ssh "${SSH_OPTS[@]}" "root@${IP}" 'mkdir -p /opt/sandtable/docs /opt/sandtable/web/js'

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
  "$ROOT/docs/试点巡检清单-M5.md" \
  "$ROOT/docs/拜访FAQ-M5.md" \
  "$ROOT/docs/P表回归-M5.md" \
  "root@${IP}:/opt/sandtable/docs/"

ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
chmod a+rX /opt/sandtable/web/visit.html /opt/sandtable/web/js/m3-mock-llm.js /opt/sandtable/docs/*-M5.md 2>/dev/null || chmod -R a+rX /opt/sandtable/web
cd /opt/sandtable/server && source venv/bin/activate && systemctl restart sandtable
sleep 3
systemctl is-active sandtable
REMOTE

echo "==> 外网抽查 visit..."
VISIT_HTML="$(curl -s "http://${IP}/visit.html")"
echo "$VISIT_HTML" | grep -Fq '智能拜访 · 品牌沙盘' && echo "OK visit title" || echo "WARN: 请硬刷新"
echo "$VISIT_HTML" | grep -Fq '承诺方</th><th>内容</th><th>截止</th>' && echo "OK pilot-3 承诺截止列" || echo "WARN: 缺承诺截止列"
echo "$VISIT_HTML" | grep -Fq '未抽取到明确截止日期' && echo "OK pilot-3 承诺截止警告" || echo "WARN: 缺承诺警告文案"

echo "✅ 完成。验收 http://${IP}/visit.html · Cmd+Shift+R"
