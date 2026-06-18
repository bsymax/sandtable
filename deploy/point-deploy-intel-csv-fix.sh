#!/bin/bash
# 热修 · 情报 CSV 上传 500（import_news_csv 缺 user 参数）
# 用法: bash deploy/point-deploy-intel-csv-fix.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 情报 CSV 热修 → root@${IP}"
scp "${SSH_OPTS[@]}" "$ROOT/server/routers/intel.py" "root@${IP}:/opt/sandtable/server/routers/"
scp "${SSH_OPTS[@]}" "$ROOT/web/intel.html" "root@${IP}:/opt/sandtable/web/"
ssh "${SSH_OPTS[@]}" "root@${IP}" "chmod -R a+rX /opt/sandtable/web && systemctl restart sandtable && sleep 3 && systemctl is-active sandtable"
echo "✅ 请重新上传 intel_news_template.csv 测试"
