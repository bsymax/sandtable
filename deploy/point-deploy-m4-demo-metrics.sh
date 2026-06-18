#!/bin/bash
# 热修 · bi_csv 后补示范类目/广告/P0（佳璇 seed.apply_demo_metrics）
# 用法: bash deploy/point-deploy-m4-demo-metrics.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> M4 示范指标热修 → root@${IP}"
scp "${SSH_OPTS[@]}" "$ROOT/server/seed_m4_demo_metrics.py" "root@${IP}:/opt/sandtable/server/"
ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
cd /opt/sandtable/server
source venv/bin/activate
python3 seed_m4_demo_metrics.py
systemctl restart sandtable
sleep 3
curl -s http://127.0.0.1:8000/api/brands/profile/hegii | python3 -c "
import sys, json
m = json.load(sys.stdin).get('metrics') or {}
assert m.get('category_distribution'), '缺 category_distribution'
assert m.get('gross_margin') is not None, '缺 gross_margin'
print('OK hegii demo fields', 'gmv', m.get('gmv'), 'margin', m.get('gross_margin'))
"
REMOTE
echo "✅ 外网请硬刷新 profile.html?brand=hegii 查看类目图与品类对标"
