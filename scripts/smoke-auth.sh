# 冒烟脚本共用登录（source 本文件，勿直接执行）
# 外网 M5-C 导入后 admin 等账号已非 sand123，请设：
#   SMOKE_ADMIN_PASSWORD='...' bash scripts/m5-pilot-smoke.sh http://117.72.211.51
# 密码见服务器 pilot-users-v1.passwords.txt 或 Max 重置后的 admin 口令

SMOKE_PASSWORD="${SMOKE_PASSWORD:-sand123}"
SMOKE_ADMIN_USER="${SMOKE_ADMIN_USER:-admin}"
SMOKE_ADMIN_PASSWORD="${SMOKE_ADMIN_PASSWORD:-$SMOKE_PASSWORD}"
SMOKE_READONLY_USER="${SMOKE_READONLY_USER:-readonly}"
SMOKE_READONLY_PASSWORD="${SMOKE_READONLY_PASSWORD:-$SMOKE_PASSWORD}"

smoke_login_json() {
  local user="$1"
  local pwd="${2:-$SMOKE_PASSWORD}"
  curl -s -X POST "${SMOKE_BASE:?}/api/auth/login" \
    -H 'Content-Type: application/json' \
    -d "{\"username\":\"$user\",\"password\":\"$pwd\"}"
}

smoke_login_token() {
  local user="$1"
  local pwd="${2:-$SMOKE_PASSWORD}"
  smoke_login_json "$user" "$pwd" | python3 -c "
import sys, json
d = json.load(sys.stdin)
t = d.get('token') or ''
if not t and d.get('detail'):
    print('', file=sys.stderr)
    sys.stderr.write(f\"login {sys.argv[1]} 失败: {d.get('detail')}\n\")
print(t)
" "$user"
}
