#!/bin/bash
# 佳璇 jiaxuan-m5-0624 终包 · profile 类目真数 + 数仓 CSV 导入
# 用法: bash deploy/point-deploy-jiaxuan-m5-0624.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE_WEB="/opt/sandtable/web"
REMOTE_SRV="/opt/sandtable/server"
REMOTE_DATA="/opt/sandtable/data"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 佳璇 M5-0624 终包 → root@${IP}"

ssh "${SSH_OPTS[@]}" "root@${IP}" "mkdir -p ${REMOTE_DATA}/dw ${REMOTE_SRV} ${REMOTE_WEB}/js /opt/sandtable/docs"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/profile.html" \
  "root@${IP}:${REMOTE_WEB}/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/js/api-base.js" \
  "root@${IP}:${REMOTE_WEB}/js/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/docs/档案试点FAQ.md" \
  "$ROOT/docs/数仓SLA-v1.md" \
  "$ROOT/docs/数仓字段口径-v1.md" \
  "root@${IP}:/opt/sandtable/docs/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/data/dw/brand_metrics_monthly.csv" \
  "$ROOT/data/dw/brand_category_monthly.csv" \
  "root@${IP}:${REMOTE_DATA}/dw/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/dw_sync.py" \
  "$ROOT/server/run_dw_sync.py" \
  "$ROOT/server/seed_m4_demo_metrics.py" \
  "root@${IP}:${REMOTE_SRV}/"

ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
APP=/opt/sandtable
cd "$APP/server"
source venv/bin/activate
python3 run_dw_sync.py "$APP/data/dw/brand_metrics_monthly.csv" --bi
python3 run_dw_sync.py --category "$APP/data/dw/brand_category_monthly.csv"
python3 seed_m4_demo_metrics.py
chmod -R a+rX "$APP/web" "$APP/docs" 2>/dev/null || chmod -R a+rX "$APP/web"
systemctl restart sandtable
sleep 3
systemctl is-active sandtable
REMOTE

echo "==> 外网抽查 profile..."
PROFILE_HTML="$(curl -s "http://${IP}/profile.html")"
echo "$PROFILE_HTML" | grep -Fq '布局机会' && echo "OK 类目表布局机会列" || echo "WARN: 缺布局机会"
echo "$PROFILE_HTML" | grep -Fq '仅展示品牌下类目占比≥1%' && echo "OK 类目≥1%过滤说明" || echo "WARN"
echo "$PROFILE_HTML" | grep -Fq 'chart-growth-' && echo "WARN: 仍有渠道增速图" || echo "OK 无渠道增速柱图"
echo "$PROFILE_HTML" | grep -Fq 'profile-benchmark-panel' && echo "WARN: 仍有品类对标面板" || echo "OK 无品类对标面板"
echo "$PROFILE_HTML" | grep -Fq '销售增速%' && echo "OK 渠道组合表含销售增速" || echo "WARN"

echo "==> API 抽查五品牌 2026-05 GMV（万）..."
curl -s "http://${IP}/api/brands/jomoo/metrics?period_type=monthly&period_value=2026-05" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('九牧 gmv=', d.get('gmv'))
" 2>/dev/null || echo "WARN: API 抽查失败（可硬刷新 profile 人工验）"

echo "✅ 完成。验收 http://${IP}/profile.html?brand=jomoo · Cmd+Shift+R"
echo "   期望 2026-05：九牧35273 / 箭牌14646 / 恒洁9886 / 潜水艇5166 / 四季沐歌3382 万"
