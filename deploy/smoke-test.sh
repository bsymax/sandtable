#!/bin/bash
# 部署后冒烟测试（本机或服务器均可）
# 用法: bash deploy/smoke-test.sh [http://公网IP]
BASE="${1:-http://127.0.0.1}"

echo "==> 冒烟测试 ${BASE}"

check() {
  local path="$1" expect="$2"
  local code body
  code=$(curl -s -o /tmp/sandtable-smoke.out -w "%{http_code}" --max-time 15 "${BASE}${path}")
  body=$(head -c 200 /tmp/sandtable-smoke.out)
  if [[ "$code" == "200" ]] && echo "$body" | grep -q "$expect"; then
    echo "  OK  ${path}"
  else
    echo "  FAIL ${path} (HTTP ${code}) ${body}"
    return 1
  fi
}

check "/api/brands" "midea" || check "/api/brands" "name"
check "/api/health" "brand"
check "/" "工作台"
check "/profile.html" "品牌"
check "/visit.html" "拜访"
check "/intel.html" "情报"
check "/docs" "swagger" || check "/docs" "openapi"

echo "==> 完成"
