#!/bin/bash
# D-X-M3-2 自动化 smoke（LLM 全关 + 登录权限）
# 用法: bash scripts/dx-m3-smoke.sh [http://127.0.0.1:8000]
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
    admin) pwd="$SMOKE_ADMIN_PASSWORD" ;;
    readonly) pwd="$SMOKE_READONLY_PASSWORD" ;;
    zhou|demo) pwd="$SMOKE_PASSWORD" ;;
  esac
  smoke_login_token "$user" "$pwd"
}

echo "==> D-X-M3 smoke @ $BASE"
echo ""

echo "-- 1. LLM 状态（应 enabled=false）--"
if [ "${M4_SMOKE:-}" = "1" ]; then
  echo "  SKIP M4 外网 LLM 可开启"
  ok "M4 跳过 LLM 全关检查"
else
LLM=$(curl -s "$BASE/api/llm/status")
echo "$LLM" | python3 -c "
import sys,json
d=json.load(sys.stdin)
assert d.get('enabled') is False, 'LLM 应关闭: '+str(d)
print('enabled=false configured='+str(d.get('configured')))
" && ok "LLM 全关" || bad "LLM 状态"
fi

echo ""
echo "-- 2. 五路 API 降级（source=fallback 或 503/ai_summary=null）--"
ADMIN=$(login admin)

check_json() {
  local label="$1" path="$2" method="${3:-GET}" body="${4:-}"
  local tmp
  tmp=$(mktemp)
  if [ "$method" = "POST" ]; then
    code=$(curl -s -o "$tmp" -w "%{http_code}" -X POST "$BASE$path" \
      -H "Authorization: Bearer $ADMIN" -H 'Content-Type: application/json' -d "${body:-{}}")
  else
    code=$(curl -s -o "$tmp" -w "%{http_code}" "$BASE$path" -H "Authorization: Bearer $ADMIN")
  fi
  if python3 - "$label" "$code" "$tmp" <<'PY'
import sys, json
label, code, path = sys.argv[1], int(sys.argv[2]), sys.argv[3]
raw = open(path).read()
try:
    d = json.loads(raw) if raw.strip() else {}
except Exception:
    print(f"{label}: 非 JSON HTTP {code}")
    sys.exit(1)
src = d.get("source")
if src == "fallback":
    print(f"{label}: source=fallback")
    sys.exit(0)
if label.startswith("intel-refresh") and code == 503:
    print(f"{label}: HTTP 503（LLM 关，预期）")
    sys.exit(0)
if label.startswith("intel-refresh") and code == 502:
    print(f"{label}: HTTP 502（LLM 网关失败，前端降级）")
    sys.exit(0)
if label.startswith("intel-refresh") and d.get("source") == "fallback":
    print(f"{label}: source=fallback")
    sys.exit(0)
if label.startswith("feed-ai") and d.get("ai_summary") in (None, "") and d.get("llm_enabled") is False:
    print(f"{label}: ai_summary=null llm_enabled=false")
    sys.exit(0)
if label.startswith("feed-ai") and d.get("ai_summary"):
    print(f"{label}: ai_summary={str(d.get('ai_summary'))[:40]}")
    sys.exit(0)
if label.startswith("feed-ai") and d.get("original_summary") and d.get("ai_summary") in (None, ""):
    print(f"{label}: ai_summary 空，降级 original_summary")
    sys.exit(0)
print(f"{label}: 意外 HTTP {code} body={raw[:120]}")
sys.exit(1)
PY
  then ok "$label"; else bad "$label"; fi
  rm -f "$tmp"
}

check_json "路1-工作台" "/api/dashboard/summary-line"
check_json "路2-档案Tab1" "/api/brands/profile/jomoo/ai/blurb" POST
check_json "路3-档案Tab2" "/api/brands/profile/jomoo/ai/strategy" POST
RID=$(curl -s "$BASE/api/records?limit=1" -H "Authorization: Bearer $ADMIN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['id'] if d else '')")
if [ -n "$RID" ]; then
  check_json "路4-拜访纪要" "/api/records/$RID/ai/extract" POST
else
  bad "路4-拜访纪要（无 record 样本）"
fi
check_json "路5-intel-summary" "/api/intel/briefing/jomoo/ai/summary" POST
check_json "intel-refresh" "/api/intel/briefing/jomoo/ai/refresh" POST
NEWS_ID=$(curl -s "$BASE/api/intel/news?limit=1" -H "Authorization: Bearer $ADMIN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['id'] if d else '')" 2>/dev/null || echo "")
if [ -n "$NEWS_ID" ]; then
  check_json "feed-ai" "/api/intel/feed/ai-summary/news/$NEWS_ID"
fi

echo ""
echo "-- 3. 登录权限（M3-A）--"
ZHOU=$(login zhou)
BC=$(curl -s "$BASE/api/brands" -H "Authorization: Bearer $ZHOU" \
  | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
[ "$BC" = "1" ] && ok "zhou 仅 1 品牌" || bad "zhou 品牌数=$BC 期望1"

CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/brands/profile/hegii" \
  -H "Authorization: Bearer $ZHOU")
[ "$CODE" = "403" ] && ok "zhou 访问恒洁档案 403" || bad "zhou hegii HTTP $CODE 期望403"

AC=$(curl -s "$BASE/api/brands" -H "Authorization: Bearer $ADMIN" \
  | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
[ "$AC" = "5" ] && ok "admin 5 品牌" || bad "admin 品牌数=$AC 期望5"

echo ""
echo "-- 4. 静态页 M3 标记（本机 5510，可选）--"
STATIC="${STATIC_BASE:-http://127.0.0.1:5510/web}"
if curl -s -o /dev/null -w "" --max-time 2 "$STATIC/index.html" 2>/dev/null; then
  curl -s "$STATIC/profile.html" | grep -q "m3-config.js" && ok "profile 含 m3-config" || bad "profile 缺 m3-config"
  curl -s "$STATIC/visit.html" | grep -q "m3-mock-llm.js" && ok "visit 含 M3 LLM" || bad "visit 缺 M3"
  curl -s "$STATIC/intel.html" | grep -q "refreshAiBriefing" && ok "intel 含 AI 简报" || bad "intel 缺 AI"
else
  echo "  SKIP 5510 未起（设 STATIC_BASE 或启静态服务）"
fi

echo ""
echo "==> 结果: PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ]
