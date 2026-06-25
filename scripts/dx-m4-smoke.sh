#!/bin/bash
# D-X-M4 smoke：M3 基线 + 只读禁写 + LLM 审计 + 数仓 latest-period
# 用法: bash scripts/dx-m4-smoke.sh [http://127.0.0.1:8000]
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

login() {
  local user="$1"
  local pwd="$SMOKE_PASSWORD"
  case "$user" in
    "$SMOKE_ADMIN_USER") pwd="$SMOKE_ADMIN_PASSWORD" ;;
    "$SMOKE_READONLY_USER") pwd="$SMOKE_READONLY_PASSWORD" ;;
  esac
  smoke_login_token "$user" "$pwd"
}

echo "==> D-X-M4 smoke @ $BASE"
echo ""

echo "-- 0. 继承 M3 smoke（跳过 LLM 全关项，M4 外网 LLM 可开）--"
M3_FAIL=0
if M4_SMOKE=1 bash "$ROOT/scripts/dx-m3-smoke.sh" "$BASE"; then
  ok "M3 回归通过"
else
  M3_FAIL=1
  echo "  WARN M3 继承项有失败（M4 以外网增量为准）"
fi

echo ""
echo "-- 1. M4-A readonly 禁写（403）--"
RO=$(login "$SMOKE_READONLY_USER")
for spec in \
  "POST|/api/visits|{\"brand_id\":1,\"visit_date\":\"2026-06-11\",\"visit_type\":\"regular\",\"purpose\":\"smoke\"}" \
  "PUT|/api/brands/profile/jomoo|{}" \
  "POST|/api/intel/news|{\"title\":\"smoke\",\"content\":\"c\",\"brand_id\":1}" \
  "POST|/api/intel/briefing/jomoo/refresh|{}"
do
  IFS='|' read -r method path body <<< "$spec"
  code=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$BASE$path" \
    -H "Authorization: Bearer $RO" -H 'Content-Type: application/json' -d "$body")
  if [ "$code" = "403" ]; then
    ok "$method $path → 403"
  else
    bad "$method $path → HTTP $code 期望403"
  fi
done

echo ""
echo "-- 2. M4-B LLM 状态含配额字段 + 审计接口 --"
ADMIN=$(login "$SMOKE_ADMIN_USER")
if curl -s "$BASE/api/llm/status" -H "Authorization: Bearer $ADMIN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for k in ('daily_cap', 'user_daily_cap', 'readonly_llm'):
    assert k in d, f'缺字段 {k}'
print('caps', d['daily_cap'], d['user_daily_cap'])
"; then
  ok "LLM status 配额字段"
else
  bad "LLM status 配额字段"
fi

code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/llm/audit?limit=5" -H "Authorization: Bearer $ADMIN")
[ "$code" = "200" ] && ok "admin GET /api/llm/audit" || bad "audit HTTP $code"

code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/llm/audit?limit=5" -H "Authorization: Bearer $RO")
[ "$code" = "403" ] && ok "readonly 禁 audit" || bad "readonly audit HTTP $code 期望403"

echo ""
echo "-- 3. M4-C 数仓 latest-period --"
if curl -s "$BASE/api/dw/latest-period?name_key=jomoo" -H "Authorization: Bearer $ADMIN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert d.get('name_key') == 'jomoo'
assert 'period_value' in d
print('period', d.get('period_value'), 'gmv', d.get('gmv'))
"; then
  ok "dw/latest-period jomoo"
else
  bad "dw/latest-period"
fi

echo ""
echo "==> M4 增量结果: PASS=$PASS FAIL=$FAIL"
if [ "$M3_FAIL" -ne 0 ]; then
  echo "    （M3 继承项 WARN，不计入 M4 失败）"
fi
[ "$FAIL" -eq 0 ]
