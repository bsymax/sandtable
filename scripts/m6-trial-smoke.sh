#!/bin/bash
# M6 工程收官冒烟（117 / 本机 API + 静态页）
# 用法: bash scripts/m6-trial-smoke.sh [http://117.72.211.51]
# 不依赖试点账号导入 · 不阻塞 G1 业务试点
set -euo pipefail
BASE="${1:-http://117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0
FAIL=0

ok() { echo "  OK  $1"; PASS=$((PASS + 1)); }
bad() { echo "  FAIL $1"; FAIL=$((FAIL + 1)); }

echo "==> M6 工程冒烟 @ $BASE"

echo ""
echo "-- 1. 11 品牌 + carpoly KPI --"
if curl -sf "$BASE/api/brands" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert len(d) == 11, len(d)
"; then ok "GET /api/brands ×11"; else bad "brands 数量"; fi

if curl -sf "$BASE/api/brands/profile/carpoly" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert d.get('completeness_max') == 12
assert (d.get('metrics') or {}).get('gmv') is not None
"; then ok "carpoly profile+KPI"; else bad "carpoly profile"; fi

echo ""
echo "-- 2. 厨小清零 --"
for page in index.html intel.html profile.html visit.html; do
  if curl -sf "$BASE/$page" | grep -Fq '厨小'; then
    bad "$page 仍有厨小"
  else
    ok "$page 无厨小"
  fi
done

has_text() {
  local url="$1" needle="$2"
  curl -sf "$url" | python3 -c "import sys; sys.exit(0 if sys.stdin.read().find('$needle')>=0 else 1)" 2>/dev/null
}

echo ""
echo "-- 3. 工具包 + 拜访导入 --"
has_text "$BASE/toolkit/talking-points.html" "tp-report-doc" && ok "talking-points 页" || bad "talking-points"
has_text "$BASE/toolkit/brand-report.html" "talking-points" && ok "brand-report→谈参" || bad "brand-report"
has_text "$BASE/visit.html" "历史导入" && ok "visit 历史导入 Tab" || bad "visit 导入"
has_text "$BASE/visit.html" "填写说明" && ok "visit 双表头模板" || bad "visit 模板"

echo ""
echo "-- 4. LLM 配额 --"
if curl -sf "$BASE/api/llm/status" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert d.get('daily_cap', 0) >= 5000
assert d.get('user_daily_cap', 0) >= 200
"; then ok "LLM quota 5000/200"; else bad "LLM quota"; fi

echo ""
echo "-- 5. Tab2 规则 fallback（前端补丁） --"
has_text "$BASE/profile.html" "isLegacyStrategySeed" && ok "profile strategy fallback" || bad "profile strategy"

echo ""
echo "-- 6. M5 回归（可选 · 需 SMOKE_ADMIN_PASSWORD） --"
if [ -n "${SMOKE_ADMIN_PASSWORD:-}" ] || curl -sf -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/json' -d '{"username":"admin","password":"sand123"}' | grep -q '"token"'; then
  if SMOKE_ADMIN_PASSWORD="${SMOKE_ADMIN_PASSWORD:-sand123}" bash "$ROOT/scripts/m5-pilot-smoke.sh" "$BASE"; then
    ok "M5 回归"
  else
    bad "M5 回归（可设 SMOKE_ADMIN_PASSWORD 后重跑）"
  fi
else
  echo "  SKIP M5 回归（117 admin 非默认密码 · 不阻塞工程 tag）"
fi

echo ""
echo "==> 通过 $PASS · 失败 $FAIL"
[ "$FAIL" -eq 0 ]
