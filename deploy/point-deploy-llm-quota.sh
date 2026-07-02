#!/bin/bash
# 热修 · LLM 日配额：全站 5000 / 用户 200（M6 试点）
set -euo pipefail

IP="${1:-117.72.211.51}"
SSH_OPTS=(-o ConnectTimeout=30)

echo ">>> 更新 ${IP} LLM 配额并重启 sandtable ..."
ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
ENV=/opt/sandtable/server/.env
cp "$ENV" "${ENV}.bak-quota-$(date +%Y%m%d-%H%M%S)"
grep -v -E '^(LLM_DAILY_CAP|LLM_USER_DAILY_CAP)=' "$ENV" > "${ENV}.tmp" || true
mv "${ENV}.tmp" "$ENV"
cat >> "$ENV" <<'EOF'

# M4-B LLM 配额（M6 试点调高）
LLM_DAILY_CAP=5000
LLM_USER_DAILY_CAP=200
EOF
chmod 600 "$ENV"
systemctl restart sandtable
sleep 3
systemctl is-active sandtable
curl -s http://127.0.0.1:8000/api/llm/status
echo ""
REMOTE

echo "✅ 外网验证: curl http://${IP}/api/llm/status  → daily_cap=5000 user_daily_cap=200"
