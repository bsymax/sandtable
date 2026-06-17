#!/bin/bash
# 上传 m3-config.js，打开档案/拜访前端 LLM 开关
# 用法: bash deploy/point-config-llm-frontend-cloud.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 上传 web/js/m3-config.js → root@${IP}:/opt/sandtable/web/js/"
scp "${SSH_OPTS[@]}" "$ROOT/web/js/m3-config.js" "root@${IP}:/opt/sandtable/web/js/"
ssh "${SSH_OPTS[@]}" "root@${IP}" 'chmod a+rX /opt/sandtable/web/js/m3-config.js'

echo ""
echo "==> 外网校验（应含 LLM_ENABLED:true 与 profile_blurb:true）..."
curl -s "http://${IP}/js/m3-config.js" | grep -E 'LLM_ENABLED|profile_blurb|record_extract' | head -6

echo ""
echo "✅ 前端 LLM 开关已上云。请外网 Cmd+Shift+R 硬刷新 profile.html / visit.html"
