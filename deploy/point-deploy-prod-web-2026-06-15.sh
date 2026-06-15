#!/bin/bash
# 定点上云 · prod-web-2026-06-15
# 佳璇 0615 补丁（销量字段 / GMV 12 周 / 类目四渠道）+ 三模块顶栏统一
# 用法: bash deploy/point-deploy-prod-web-2026-06-15.sh [IP]
# 会提示 root SSH 密码（2～3 次）
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE_WEB="/opt/sandtable/web"
REMOTE_SRV="/opt/sandtable/server"
REMOTE_DB="/opt/sandtable/database"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 部署目标: root@${IP}"
echo "    标签: prod-web-2026-06-15（0615 补丁 + 顶栏）"
echo ""

echo "==> [1/4] 上传 web 三模块..."
scp "${SSH_OPTS[@]}" \
  "$ROOT/web/profile.html" \
  "$ROOT/web/visit.html" \
  "$ROOT/web/intel.html" \
  "root@${IP}:${REMOTE_WEB}/"

echo "==> [2/4] 上传 server + 数据库补丁..."
scp "${SSH_OPTS[@]}" \
  "$ROOT/server/models.py" \
  "$ROOT/server/schemas.py" \
  "$ROOT/server/seed_brand_metrics.py" \
  "root@${IP}:${REMOTE_SRV}/"
scp "${SSH_OPTS[@]}" \
  "$ROOT/database/migrate_jiaxuan_0615.sql" \
  "root@${IP}:${REMOTE_DB}/"

echo "==> [3/4] 远程 migration + seed + 重启..."
ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
APP=/opt/sandtable
DB_PASS=$(grep -E '^DB_PASSWORD=' "$APP/server/.env" | cut -d= -f2- | tr -d '\r')

echo "-- 执行 migrate_jiaxuan_0615.sql（若已是 sales_volume 会跳过）"
mysql -u brand_app -p"${DB_PASS}" brand_sandtable 2>/dev/null <<'SQL' || true
ALTER TABLE brand_metrics
  CHANGE COLUMN orders sales_volume INT DEFAULT NULL COMMENT '销量',
  CHANGE COLUMN orders_wow sales_volume_wow DECIMAL(6,2) DEFAULT NULL COMMENT '销量环比%';
SQL

cd "$APP/server"
source venv/bin/activate
python3 seed_brand_metrics.py

chmod -R a+rX "$APP/web"
systemctl restart sandtable
sleep 2
systemctl is-active sandtable
curl -s -o /dev/null -w "brands HTTP %{http_code}\n" http://127.0.0.1:8000/api/brands
MET=$(curl -s "http://127.0.0.1:8000/api/brands/metrics/midea?limit=12")
echo "$MET" | python3 -c "import sys,json; d=json.load(sys.stdin); print('metrics weeks:', len(d), 'fields:', 'sales_volume' if d and 'sales_volume' in d[0] else 'orders')"
REMOTE

echo ""
echo "==> [4/4] 外网冒烟..."
bash "$ROOT/deploy/smoke-test.sh" "http://${IP}" || true
echo ""
echo "✅ 完成。请外网 Cmd+Shift+R 硬刷新："
echo "   http://${IP}/profile.html  （KPI 应显示「销量」、GMV 折线 ≥2 点）"
echo "   http://${IP}/visit.html   （顶栏 › 分隔）"
echo "   http://${IP}/intel.html"
