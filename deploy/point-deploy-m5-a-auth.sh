#!/bin/bash
# M5-A 账号体系上云：migration 提示 + auth 后端 + 登录/改密/admin 页
# 用法: bash deploy/point-deploy-m5-a-auth.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> M5-A 上云 → root@${IP}"
echo "    上云后请在服务器执行一次 migration（见文末）"

ssh "${SSH_OPTS[@]}" "root@${IP}" 'mkdir -p /opt/sandtable/scripts /opt/sandtable/database /opt/sandtable/server/routers /opt/sandtable/web/js'

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/auth_utils.py" \
  "$ROOT/server/models.py" \
  "$ROOT/server/schemas.py" \
  "$ROOT/server/deps_auth.py" \
  "$ROOT/server/requirements.txt" \
  "root@${IP}:/opt/sandtable/server/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/routers/auth.py" \
  "root@${IP}:/opt/sandtable/server/routers/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/login.html" \
  "$ROOT/web/change-password.html" \
  "$ROOT/web/admin-users.html" \
  "root@${IP}:/opt/sandtable/web/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/js/auth.js" \
  "$ROOT/web/js/shell.js" \
  "root@${IP}:/opt/sandtable/web/js/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/database/migrate_m5_auth.sql" \
  "root@${IP}:/opt/sandtable/database/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/server/bootstrap_local_db.py" \
  "root@${IP}:/opt/sandtable/server/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/scripts/import-pilot-users.py" \
  "$ROOT/scripts/m5-pilot-smoke.sh" \
  "root@${IP}:/opt/sandtable/scripts/"

ssh "${SSH_OPTS[@]}" "root@${IP}" 'chmod +x /opt/sandtable/scripts/import-pilot-users.py /opt/sandtable/scripts/m5-pilot-smoke.sh 2>/dev/null || true'

ssh "${SSH_OPTS[@]}" "root@${IP}" bash <<'REMOTE'
set -euo pipefail
cd /opt/sandtable/server
source venv/bin/activate
pip install -q bcrypt
pip install -q -r requirements.txt
python3 bootstrap_local_db.py
systemctl restart sandtable
sleep 4
systemctl is-active sandtable
REMOTE

echo "==> 外网验证 login 字段..."
curl -s -X POST "http://${IP}/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"sand123"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'must_change_password' in d; print('must_change_password', d['must_change_password'])"

echo "✅ M5-A 补丁已上云。请 SSH 执行 migration + bash scripts/m5-pilot-smoke.sh http://${IP}"
