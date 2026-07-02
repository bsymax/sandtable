#!/bin/bash
# M6-A · 11 品牌落库（佳璇 J-1）
# 用法: bash deploy/point-deploy-m6-a-11brands.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> M6-A 11 品牌 → root@${IP}"

ssh "${SSH_OPTS[@]}" "root@${IP}" 'mkdir -p /opt/sandtable/data /opt/sandtable/server /opt/sandtable/database'

scp "${SSH_OPTS[@]}" \
  "$ROOT/data/brands_master.json" \
  "root@${IP}:/opt/sandtable/data/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/seed_m6_brands.py" \
  "root@${IP}:/opt/sandtable/server/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/database/migrate_m6_11_brands.sql" \
  "root@${IP}:/opt/sandtable/database/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/docs/品牌主数据-M6-11品牌.md" \
  "root@${IP}:/opt/sandtable/docs/" 2>/dev/null || \
  ssh "${SSH_OPTS[@]}" "root@${IP}" 'mkdir -p /opt/sandtable/docs' && \
  scp "${SSH_OPTS[@]}" "$ROOT/docs/品牌主数据-M6-11品牌.md" "root@${IP}:/opt/sandtable/docs/"

ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
cd /opt/sandtable/server && source venv/bin/activate
python3 seed_m6_brands.py
systemctl restart sandtable
sleep 2
curl -sf "http://127.0.0.1:8000/api/brands" | python3 -c "import sys,json; d=json.load(sys.stdin); print('brands', len(d))"
REMOTE

echo "✅ M6-A 完成。外网: curl http://${IP}/api/brands | 应 11 条"
