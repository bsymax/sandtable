#!/bin/bash
# 开开 kaikai-m6-0630 · 厨小清零 + mock 过滤 + 名单模板
# 用法: bash deploy/point-deploy-kaikai-m6-0630.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 开开 M6-0630 → root@${IP}"

ssh "${SSH_OPTS[@]}" "root@${IP}" 'mkdir -p /opt/sandtable/web/js /opt/sandtable/server/routers /opt/sandtable/docs/templates /opt/sandtable/data'

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/index.html" \
  "$ROOT/web/intel.html" \
  "root@${IP}:/opt/sandtable/web/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/js/m3-config.js" \
  "$ROOT/web/js/m3-mock-llm.js" \
  "$ROOT/web/js/shell.js" \
  "root@${IP}:/opt/sandtable/web/js/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/config.py" \
  "$ROOT/server/routers/intel.py" \
  "$ROOT/server/seed_m6_brands.py" \
  "root@${IP}:/opt/sandtable/server/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/routers/intel.py" \
  "root@${IP}:/opt/sandtable/server/routers/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/data/brands_master.json" \
  "root@${IP}:/opt/sandtable/data/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/docs/templates/pilot-users-m6.example.csv" \
  "$ROOT/docs/templates/m6-group-announcement.md" \
  "root@${IP}:/opt/sandtable/docs/templates/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/scripts/import-pilot-users.py" \
  "root@${IP}:/opt/sandtable/scripts/"

ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
chmod -R a+rX /opt/sandtable/web/index.html /opt/sandtable/web/intel.html /opt/sandtable/web/js /opt/sandtable/data /opt/sandtable/docs/templates
cd /opt/sandtable/server && source venv/bin/activate
python3 seed_m6_brands.py
systemctl restart sandtable
sleep 3
systemctl is-active sandtable
REMOTE

echo "==> 外网抽查..."
for f in index.html intel.html; do
  BODY="$(curl -s "http://${IP}/${f}")"
  echo "$BODY" | grep -Fq '厨小' && echo "WARN ${f} 仍有厨小" || echo "OK ${f} 无厨小"
done
curl -sf "http://${IP}/api/intel/news?limit=5" | grep -Fq '美的' && echo "WARN 新闻仍有 demo" || echo "OK 新闻 mock 已过滤（或未登录）"

echo "✅ 完成。正式名单: docs/templates/pilot-users-m6.csv · 导入见 deploy/point-deploy-m6-b-import.sh"
