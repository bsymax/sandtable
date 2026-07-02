#!/bin/bash
# 佳璇 jiaxuan-m6-0701-02 终包 · 档案 12 分 + 建材数仓 + 谈参 + org 图
# 用法: bash deploy/point-deploy-jiaxuan-m6-0701.sh [IP]
# 前置: bash deploy/point-deploy-m6-a-11brands.sh（id=11 carpoly）
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE_WEB="/opt/sandtable/web"
REMOTE_SRV="/opt/sandtable/server"
REMOTE_DATA="/opt/sandtable/data"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 佳璇 M6-0701-02 终包 → root@${IP}"

ssh "${SSH_OPTS[@]}" "root@${IP}" "mkdir -p ${REMOTE_DATA}/dw ${REMOTE_SRV}/routers ${REMOTE_SRV}/uploads/org ${REMOTE_WEB}/js ${REMOTE_WEB}/toolkit /opt/sandtable/docs"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/profile.html" \
  "root@${IP}:${REMOTE_WEB}/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/toolkit/talking-points.html" \
  "$ROOT/web/toolkit/brand-report.html" \
  "root@${IP}:${REMOTE_WEB}/toolkit/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/js/shell.js" \
  "root@${IP}:${REMOTE_WEB}/js/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/docs/档案试点FAQ.md" \
  "$ROOT/docs/数仓SLA-v1.md" \
  "$ROOT/docs/品牌主数据-M6-11品牌.md" \
  "$ROOT/docs/发给Max-M6佳璇终包说明.md" \
  "root@${IP}:/opt/sandtable/docs/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/data/brands_master.json" \
  "root@${IP}:${REMOTE_DATA}/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/data/dw/brand_metrics_monthly.csv" \
  "$ROOT/data/dw/brand_category_monthly.csv" \
  "$ROOT/data/dw/transform_brand_source.py" \
  "$ROOT/data/dw/transform_category_source.py" \
  "$ROOT/data/dw/transform_jc_brand_source.py" \
  "$ROOT/data/dw/transform_jc_category_source.py" \
  "root@${IP}:${REMOTE_DATA}/dw/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/main.py" \
  "$ROOT/server/models.py" \
  "$ROOT/server/schemas.py" \
  "$ROOT/server/completeness.py" \
  "$ROOT/server/org_structure.py" \
  "$ROOT/server/seed.py" \
  "$ROOT/server/seed_m6_brands.py" \
  "$ROOT/server/bootstrap_local_db.py" \
  "$ROOT/server/requirements.txt" \
  "root@${IP}:${REMOTE_SRV}/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/routers/profile.py" \
  "root@${IP}:${REMOTE_SRV}/routers/"

ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
APP=/opt/sandtable
cd "$APP/server"
source venv/bin/activate
pip install -q -r requirements.txt
python3 seed_m6_brands.py
python3 seed.py
chmod -R a+rX "$APP/web" "$APP/docs" "$APP/data/dw" 2>/dev/null || chmod -R a+rX "$APP/web"
systemctl restart sandtable
sleep 3
systemctl is-active sandtable
curl -sf "http://127.0.0.1:8000/api/brands" | python3 -c "import sys,json; print('brands', len(json.load(sys.stdin)))"
curl -sf "http://127.0.0.1:8000/api/brands/profile/carpoly" | python3 -c "import sys,json; d=json.load(sys.stdin); print('carpoly completeness', d.get('completeness_score'), '/', d.get('completeness_max'))"
REMOTE

echo "==> 外网抽查..."
PROFILE_HTML="$(curl -s "http://${IP}/profile.html")"
echo "$PROFILE_HTML" | grep -Fq '十一品牌' && echo "OK 十一品牌 subtitle" || echo "WARN"
echo "$PROFILE_HTML" | grep -Fq "carpoly" && echo "OK 嘉宝莉 Tab" || echo "WARN 嘉宝莉 Tab"
echo "$PROFILE_HTML" | grep -Fq '厨小' && echo "WARN: 仍有厨小" || echo "OK 无厨小"
echo "$PROFILE_HTML" | grep -Fq '五品牌' && echo "WARN: 仍写五品牌" || echo "OK 非五品牌文案"
curl -sf "http://${IP}/toolkit/talking-points.html" | head -c 200 | grep -Fq '谈参' && echo "OK 谈参页" || echo "WARN 谈参页"

echo "✅ 完成。验收 http://${IP}/profile.html · http://${IP}/toolkit/talking-points.html"
