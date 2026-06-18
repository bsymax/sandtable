#!/bin/bash
# D-X-M4 smoke：M3 基线 + 只读禁写 + LLM 审计 + 数仓 latest-period
# 用法: bash scripts/dx-m4-smoke.sh [http://127.0.0.1:8000]
set -euo pipefail
BASE="${1:-http://127.0.0.1:8000}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0
FAIL=0

ok() { echo "  OK  $1"; PASS=$((PASS + 1)); }
bad() { echo "  FAIL $1"; FAIL=$((FAIL + 1)); }

login() {
  local user="$1"
  curl -s -X POST "$BASE/api/auth/login" \
    -H 'Content-Type: application/json' \
    -d "{\"username\":\"$user\",\"password\":\"sand123\"}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))"
}

echo "==> D-X-M4 smoke @ $BASE"
echo ""

echo "-- 0. 继承 M3 smoke（跳过 LLM 全关项，M4 外网 LLM 可开）--"
if M4_SMOKE=1 bash "$ROOT/scripts/dx-m3-smoke.sh" "$BASE"; then
  ok "M3 smoke 通过"
else
  bad "M3 smoke 失败"
fi

echo ""
echo "-- 1. M4-A readonly 禁写（403）--"
RO=$(login readonly)
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
ADMIN=$(login admin)
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
[ "$FAIL" -eq 0 ]
