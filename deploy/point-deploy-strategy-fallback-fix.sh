#!/bin/bash
# Tab2 竞争/机会 · 卫浴5旧seed清库 + 前端规则 fallback + LLM失败走新规则
# 用法: bash deploy/point-deploy-strategy-fallback-fix.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> Tab2 规则 fallback 修复 → root@${IP}"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/profile.html" \
  "root@${IP}:/opt/sandtable/web/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/seed.py" \
  "$ROOT/server/llm_prompts.py" \
  "root@${IP}:/opt/sandtable/server/"

ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
cd /opt/sandtable/server
source venv/bin/activate
python3 seed.py
systemctl restart sandtable
sleep 3
systemctl is-active sandtable
REMOTE

echo "==> 外网抽查 jomoo profile Tab2 应含【渠道市占】而非旧单行 seed..."
curl -sf "http://${IP}/profile.html" | grep -Fq 'isLegacyStrategySeed' && echo "OK profile.html 已更新" || echo "WARN 请 Cmd+Shift+R"

echo "✅ 完成。硬刷新 http://${IP}/profile.html?brand=jomoo Tab2 验证"
