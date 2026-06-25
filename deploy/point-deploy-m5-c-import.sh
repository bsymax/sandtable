#!/bin/bash
# M5-C 试点名单导入 · legacy brand_key 映射 + dry-run/正式导入
# 用法:
#   bash deploy/point-deploy-m5-c-import.sh              # dry-run
#   bash deploy/point-deploy-m5-c-import.sh --apply      # 正式导入
#   bash deploy/point-deploy-m5-c-import.sh --apply /path/to/custom.csv
set -euo pipefail
IP="${1:-117.72.211.51}"
if [[ "${1:-}" == "--apply" || "${1:-}" == "--dry-run" ]]; then
  IP="117.72.211.51"
fi
APPLY=0
CSV=""
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --dry-run) APPLY=0 ;;
    *.csv) CSV="$arg" ;;
    [0-9]*.[0-9]*.[0-9]*.[0-9]*) IP="$arg" ;;
  esac
done
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)
CSV="${CSV:-$ROOT/docs/templates/pilot-users-v1.example.csv}"
REMOTE_CSV="/opt/sandtable/data/pilot-users-v1.csv"

if [[ ! -f "$CSV" ]]; then
  echo "错误: CSV 不存在: $CSV"
  exit 1
fi

echo "==> M5-C 名单导入 @ ${IP} · $(basename "$CSV") · apply=${APPLY}"

scp "${SSH_OPTS[@]}" \
  "$ROOT/scripts/import-pilot-users.py" \
  "root@${IP}:/opt/sandtable/scripts/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/brand_keys.py" \
  "root@${IP}:/opt/sandtable/server/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/data/brands_master.json" \
  "root@${IP}:/opt/sandtable/data/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/routers/auth.py" \
  "root@${IP}:/opt/sandtable/server/routers/"

scp "${SSH_OPTS[@]}" \
  "$CSV" \
  "root@${IP}:${REMOTE_CSV}"

ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s "$REMOTE_CSV" "$APPLY" <<'REMOTE'
set -euo pipefail
REMOTE_CSV="$1"
APPLY="$2"
cd /opt/sandtable/server
source venv/bin/activate
systemctl restart sandtable
sleep 3

echo "==> dry-run"
python3 ../scripts/import-pilot-users.py "$REMOTE_CSV" --dry-run --strict

if [[ "$APPLY" == "1" ]]; then
  echo "==> 正式导入"
  python3 ../scripts/import-pilot-users.py "$REMOTE_CSV" --strict
  echo "==> 用户数"
  DB_PASS=$(grep -E '^DB_PASSWORD=' /opt/sandtable/server/.env | cut -d= -f2- | tr -d '\r')
  mysql -u brand_app -p"${DB_PASS}" brand_sandtable -N -e "SELECT COUNT(*) FROM users WHERE is_active=1;"
  mysql -u brand_app -p"${DB_PASS}" brand_sandtable -N -e "SELECT role, COUNT(*) FROM users WHERE is_active=1 GROUP BY role;"
else
  echo "（未 --apply，仅 dry-run。正式导入: bash deploy/point-deploy-m5-c-import.sh --apply）"
fi
REMOTE

echo ""
echo "✅ M5-C 完成。admin 复核: http://${IP}/admin-users.html"
