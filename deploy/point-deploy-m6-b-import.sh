#!/bin/bash
# M6-B · 正式采销名单导入（开开 pilot-users-m6.csv）
#
# 用法:
#   bash deploy/point-deploy-m6-b-import.sh                    # dry-run（默认 CSV）
#   bash deploy/point-deploy-m6-b-import.sh --apply          # 正式导入（须环境变量）
#   bash deploy/point-deploy-m6-b-import.sh --apply /path/to.csv
#
# 正式导入前设置统一密码（勿写入 git / 脚本）:
#   export M6_PRESET_PASSWORD='……'
#   bash deploy/point-deploy-m6-b-import.sh --apply
set -euo pipefail
IP="117.72.211.51"
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
CSV="${CSV:-$ROOT/docs/templates/pilot-users-m6.csv}"
REMOTE_CSV="/opt/sandtable/data/pilot-users-m6.csv"

if [[ ! -f "$CSV" ]]; then
  echo "错误: CSV 不存在: $CSV"
  echo "请将开开正式名单放到 docs/templates/pilot-users-m6.csv"
  exit 1
fi

if [[ "$APPLY" == "1" && -z "${M6_PRESET_PASSWORD:-}" ]]; then
  echo "错误: 正式导入须先 export M6_PRESET_PASSWORD='统一初始密码'（勿写入 git）"
  exit 1
fi

echo "==> M6-B 名单导入 @ ${IP} · $(basename "$CSV") · apply=${APPLY}"

scp "${SSH_OPTS[@]}" \
  "$ROOT/scripts/import-pilot-users.py" \
  "root@${IP}:/opt/sandtable/scripts/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/brand_keys.py" \
  "root@${IP}:/opt/sandtable/server/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/data/brands_master.json" \
  "root@${IP}:/opt/sandtable/data/"

scp "${SSH_OPTS[@]}" "$CSV" "root@${IP}:${REMOTE_CSV}"

ssh "${SSH_OPTS[@]}" "root@${IP}" M6_PRESET_PASSWORD="${M6_PRESET_PASSWORD:-}" bash -s "$REMOTE_CSV" "$APPLY" <<'REMOTE'
set -euo pipefail
REMOTE_CSV="$1"
APPLY="$2"
PRESET="${M6_PRESET_PASSWORD:-}"
cd /opt/sandtable/server
source venv/bin/activate

echo "==> 确保十一品牌已 seed"
python3 seed_m6_brands.py 2>/dev/null || true

IMPORT_ARGS=(../scripts/import-pilot-users.py "$REMOTE_CSV" --strict)
if [[ -n "$PRESET" ]]; then
  IMPORT_ARGS+=(--preset-password "$PRESET")
fi

echo "==> dry-run"
python3 "${IMPORT_ARGS[@]}" --dry-run

if [[ "$APPLY" == "1" ]]; then
  echo "==> 正式导入"
  python3 "${IMPORT_ARGS[@]}"
  echo "==> 活跃用户数"
  DB_PASS=$(grep -E '^DB_PASSWORD=' /opt/sandtable/server/.env | cut -d= -f2- | tr -d '\r')
  mysql -u brand_app -p"${DB_PASS}" brand_sandtable -N -e "SELECT COUNT(*) FROM users WHERE is_active=1;"
  mysql -u brand_app -p"${DB_PASS}" brand_sandtable -N -e "SELECT role, COUNT(*) FROM users WHERE is_active=1 GROUP BY role;"
else
  echo "（未 --apply。正式: export M6_PRESET_PASSWORD=… && bash deploy/point-deploy-m6-b-import.sh --apply）"
fi
REMOTE

echo ""
echo "✅ M6-B 完成。复核: http://${IP}/admin-users.html"
