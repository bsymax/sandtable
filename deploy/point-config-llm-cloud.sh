#!/bin/bash
# 从本机 server/.env 同步 DeepSeek LLM 配置到云上并重启
# 用法: bash deploy/point-config-llm-cloud.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_LOCAL="$ROOT/server/.env"
SSH_OPTS=(-o ConnectTimeout=30)

if [[ ! -f "$ENV_LOCAL" ]]; then
  echo "错误: 找不到 $ENV_LOCAL"
  exit 1
fi

get_env() {
  local key="$1"
  grep -E "^${key}=" "$ENV_LOCAL" | head -1 | cut -d= -f2- | tr -d '\r'
}

LLM_ENABLED="$(get_env LLM_ENABLED)"
LLM_GATEWAY_URL="$(get_env LLM_GATEWAY_URL)"
LLM_API_KEY="$(get_env LLM_API_KEY)"
LLM_MODEL="$(get_env LLM_MODEL)"
LLM_TIMEOUT_SEC="$(get_env LLM_TIMEOUT_SEC)"

for v in LLM_ENABLED LLM_GATEWAY_URL LLM_API_KEY LLM_MODEL; do
  if [[ -z "${!v}" ]]; then
    echo "错误: $ENV_LOCAL 缺少 ${v}"
    exit 1
  fi
done
[[ -z "$LLM_TIMEOUT_SEC" ]] && LLM_TIMEOUT_SEC=25

if [[ "$LLM_API_KEY" == *"在此粘贴"* ]] || [[ "$LLM_API_KEY" == sk-your* ]]; then
  echo "错误: 请先在 server/.env 填写真实 LLM_API_KEY"
  exit 1
fi

echo "==> 同步 LLM 配置 → root@${IP}:/opt/sandtable/server/.env"
echo "    model=${LLM_MODEL} gateway=${LLM_GATEWAY_URL}"

ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<REMOTE
set -euo pipefail
ENV=/opt/sandtable/server/.env
cp "\$ENV" "\${ENV}.bak-llm-\$(date +%Y%m%d-%H%M%S)"
grep -v -E '^(LLM_ENABLED|LLM_GATEWAY_URL|LLM_API_KEY|LLM_MODEL|LLM_TIMEOUT_SEC)=' "\$ENV" > "\${ENV}.tmp" || true
mv "\${ENV}.tmp" "\$ENV"
cat >> "\$ENV" <<EOF

# ---------- M3 LLM（DeepSeek 公网）----------
LLM_ENABLED=${LLM_ENABLED}
LLM_GATEWAY_URL=${LLM_GATEWAY_URL}
LLM_API_KEY=${LLM_API_KEY}
LLM_MODEL=${LLM_MODEL}
LLM_TIMEOUT_SEC=${LLM_TIMEOUT_SEC}
EOF
chmod 600 "\$ENV"
systemctl restart sandtable
sleep 4
systemctl is-active sandtable
curl -s http://127.0.0.1:8000/api/llm/status
echo ""
curl -s http://127.0.0.1:8000/api/dashboard/summary-line | head -c 200
echo ""
REMOTE

echo ""
echo "==> 外网验证..."
curl -s "http://${IP}/api/llm/status"
echo ""
curl -s "http://${IP}/api/dashboard/summary-line" | python3 -c "import sys,json; d=json.load(sys.stdin); print('source:', d.get('source'))"
echo ""
echo "✅ 云上 DeepSeek 配置完成"
