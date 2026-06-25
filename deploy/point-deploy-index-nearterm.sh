#!/bin/bash
# 工作台 · 近期待办（待拜访 + 承诺待兑现）
# 用法: bash deploy/point-deploy-index-nearterm.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 工作台上云 index.html → root@${IP}"
scp "${SSH_OPTS[@]}" "$ROOT/web/index.html" "root@${IP}:/opt/sandtable/web/"
sleep 1
HTML="$(curl -s "http://${IP}/index.html")"
echo "$HTML" | grep -Fq '待拜访' && echo "$HTML" | grep -Fq '承诺待兑现' && echo "OK 两栏近期待办" || echo "WARN: 请浏览器硬刷新验收"
echo "✅ http://${IP}/index.html · Cmd+Shift+R"
