#!/bin/bash
# 开开 kaikai-m5-0624 · 情报页搜索双列表筛选 + briefing linked 口径（后端已在主工程）
# 用法: bash deploy/point-deploy-kaikai-m5-0624.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 开开 M5-0624 → root@${IP}"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/intel.html" \
  "root@${IP}:/opt/sandtable/web/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/routers/intel.py" \
  "root@${IP}:/opt/sandtable/server/routers/"

ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
chmod a+rX /opt/sandtable/web/intel.html
systemctl restart sandtable
sleep 2
systemctl is-active sandtable
REMOTE

echo "==> 外网抽查 intel.html..."
INTEL="$(curl -s "http://${IP}/intel.html")"
echo "$INTEL" | grep -Fq 'getFilteredNews' && echo "OK 新闻搜索过滤" || echo "WARN: 缺 getFilteredNews"
echo "$INTEL" | grep -Fq 'renderNewsPaged();' && echo "OK 搜索联动新闻分页" || echo "WARN"

echo "==> briefing API 含 linked..."
curl -s "http://${IP}/api/intel/briefing/jomoo" | python3 -c "
import sys, json
d = json.load(sys.stdin)
st = sorted({a.get('status') for a in d.get('active_alerts', [])})
print('statuses', st)
print('count', len(d.get('active_alerts', [])))
"

echo "✅ 完成。验收 http://${IP}/intel.html · 搜索框同时筛预警+新闻 · Cmd+Shift+R"
