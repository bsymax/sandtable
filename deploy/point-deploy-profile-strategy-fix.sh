#!/bin/bash
# Tab2 竞争/机会 · 空库规则底稿 + LLM 修复
# 用法: bash deploy/point-deploy-profile-strategy-fix.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 上传 server 补丁 → root@${IP}"
scp "${SSH_OPTS[@]}" \
  "$ROOT/server/llm_prompts.py" \
  "root@${IP}:/opt/sandtable/server/"
scp "${SSH_OPTS[@]}" \
  "$ROOT/server/routers/profile.py" \
  "root@${IP}:/opt/sandtable/server/routers/"

echo "==> 重启 sandtable..."
ssh "${SSH_OPTS[@]}" "root@${IP}" 'systemctl restart sandtable && sleep 4 && systemctl is-active sandtable'

echo "==> 外网验证 morphy strategy..."
TOKEN=$(curl -s -X POST "http://${IP}/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"sand123"}' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["token"])')
curl -s -X POST "http://${IP}/api/brands/profile/morphy/ai/strategy" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H 'Content-Type: application/json' \
  -d '{}' | python3 -c "
import sys,json
d=json.load(sys.stdin)
c=d.get('competitive_landscape','')
print('source:', d.get('source'))
print('comp preview:', c[:80].replace(chr(10),' '))
assert 'Tab2' not in c and '暂无竞争格局' not in c, '仍为占位文案'
print('OK')
"

echo "✅ 完成。外网 profile.html?brand=morphy Tab2 硬刷新验证"
