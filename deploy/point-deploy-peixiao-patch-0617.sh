#!/bin/bash
# 培翛 M2 补丁 peixiao-m2-0617 · 承诺 brand_id 筛选 + visit.html 前端兜底
# 用法: bash deploy/point-deploy-peixiao-patch-0617.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 培翛补丁 0617 @ ${IP}"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/visit.html" \
  "root@${IP}:/opt/sandtable/web/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/routers/visits.py" \
  "root@${IP}:/opt/sandtable/server/routers/"

ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
APP=/opt/sandtable
chmod -R a+rX "$APP/web"
systemctl restart sandtable
sleep 2
curl -s -o /dev/null -w "commitments HTTP %{http_code}\n" "http://127.0.0.1:8000/api/commitments?brand_id=1"
REMOTE

echo ""
echo "✅ 外网验收："
echo "   http://${IP}/visit.html → 承诺跟踪 → 品牌筛选九阳，应只显示九阳行"
echo "   硬刷新 Cmd+Shift+R"
