#!/bin/bash
# M5 冒烟：M4 回归 + 改密/重置/admin · 登录强制改密字段
# 用法:
#   bash scripts/m5-pilot-smoke.sh [http://127.0.0.1:8000]
#   SMOKE_ADMIN_PASSWORD='...' bash scripts/m5-pilot-smoke.sh http://117.72.211.51
set -euo pipefail
BASE="${1:-http://127.0.0.1:8000}"
SMOKE_BASE="$BASE"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=smoke-auth.sh
source "$ROOT/scripts/smoke-auth.sh"
PASS=0
FAIL=0

ok() { echo "  OK  $1"; PASS=$((PASS + 1)); }
bad() { echo "  FAIL $1"; FAIL=$((FAIL + 1)); }

echo "==> M5 pilot smoke @ $BASE"
echo "    admin=$SMOKE_ADMIN_USER · 密码=${SMOKE_ADMIN_PASSWORD:+已设环境变量}${SMOKE_ADMIN_PASSWORD:-默认sand123}"

echo ""
echo "-- 0. M4 回归 --"
if SMOKE_ADMIN_PASSWORD="$SMOKE_ADMIN_PASSWORD" SMOKE_PASSWORD="$SMOKE_PASSWORD" \
   SMOKE_ADMIN_USER="$SMOKE_ADMIN_USER" SMOKE_READONLY_USER="$SMOKE_READONLY_USER" \
   SMOKE_READONLY_PASSWORD="$SMOKE_READONLY_PASSWORD" \
   M4_SMOKE=1 bash "$ROOT/scripts/dx-m4-smoke.sh" "$BASE"; then
  ok "M4 回归"
else
  bad "M4 回归有失败"
fi

echo ""
echo "-- 1. login 含 must_change_password --"
if smoke_login_json "$SMOKE_ADMIN_USER" "$SMOKE_ADMIN_PASSWORD" | python3 -c "
import sys, json
d = json.load(sys.stdin)
if not d.get('token'):
    raise SystemExit(d.get('detail') or '无 token')
assert 'must_change_password' in d, '缺 must_change_password'
print('must_change_password', d['must_change_password'])
"; then
  ok "login 字段"
else
  bad "login 字段（117 上 admin 已非 sand123 时请设 SMOKE_ADMIN_PASSWORD）"
fi

echo ""
echo "-- 2. admin 用户列表 + 重置密码 --"
ADMIN_JSON=$(smoke_login_json "$SMOKE_ADMIN_USER" "$SMOKE_ADMIN_PASSWORD")
TOKEN=$(echo "$ADMIN_JSON" | python3 -c "
import sys, json
d = json.load(sys.stdin)
t = d.get('token')
if not t:
    raise SystemExit(d.get('detail') or '无 token')
print(t)
" 2>/dev/null) || TOKEN=""
if [ -z "$TOKEN" ]; then
  bad "admin 登录失败，后续 admin 用例跳过"
else
  code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/auth/admin/users" -H "Authorization: Bearer $TOKEN")
  [ "$code" = "200" ] && ok "GET admin/users" || bad "admin/users HTTP $code"

  RO=$(smoke_login_token "$SMOKE_READONLY_USER" "$SMOKE_READONLY_PASSWORD")
  code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/auth/admin/users" -H "Authorization: Bearer $RO")
  [ "$code" = "403" ] && ok "readonly 禁 admin/users" || bad "readonly admin HTTP $code"

  echo ""
  echo "-- 3. change-password API 存在 --"
  code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/auth/change-password" \
    -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
    -d '{"old_password":"wrong","new_password":"Newpass123"}')
  [ "$code" = "400" ] && ok "change-password 校验原密码" || bad "change-password HTTP $code"
fi

echo ""
echo "==> 通过 $PASS · 失败 $FAIL"
[ "$FAIL" -eq 0 ]
