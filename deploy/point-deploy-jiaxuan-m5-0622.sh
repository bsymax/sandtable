#!/bin/bash
# 佳璇 M5 jiaxuan-m5-pilot / pilot-2 · profile + FAQ/SLA docs
# 用法: bash deploy/point-deploy-jiaxuan-m5-0622.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 佳璇 M5 合并上云 → root@${IP}"

ssh "${SSH_OPTS[@]}" "root@${IP}" 'mkdir -p /opt/sandtable/docs'

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/profile.html" \
  "root@${IP}:/opt/sandtable/web/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/docs/档案试点FAQ.md" \
  "$ROOT/docs/数仓SLA-v1.md" \
  "root@${IP}:/opt/sandtable/docs/"

ssh "${SSH_OPTS[@]}" "root@${IP}" 'chmod a+rX /opt/sandtable/web/profile.html /opt/sandtable/docs/档案试点FAQ.md /opt/sandtable/docs/数仓SLA-v1.md 2>/dev/null || chmod -R a+rX /opt/sandtable/web'

echo "==> 外网抽查 profile..."
PROFILE_HTML="$(curl -s "http://${IP}/profile.html")"
echo "$PROFILE_HTML" | grep -Fq '数据每月更新' && echo "OK subtitle" || echo "WARN: 请硬刷新"
echo "$PROFILE_HTML" | grep -Eq 'renderMetricsPeriodHint|renderTrendChartTitle' && echo "OK pilot-2 月频文案函数" || echo "WARN: 缺月频函数"
echo "$PROFILE_HTML" | grep -Fq 'renderDataAsOfHtml' && echo "WARN: 仍有顶栏数据截至" || echo "OK 无顶栏数据截至"
echo "$PROFILE_HTML" | grep -Eq 'class="m1-banner"|bi_csv|AI 生成' && echo "WARN: 仍有内部术语" || echo "OK 无 M4/bi_csv 泄露"
ssh "${SSH_OPTS[@]}" "root@${IP}" "grep -Fq 'YYYY-MM 当月' /opt/sandtable/docs/档案试点FAQ.md" \
  && echo "OK FAQ 月频口径（服务器文件）" || echo "WARN: FAQ 未更新或路径不对"

echo "✅ 完成。验收 http://${IP}/profile.html?brand=micoe · Cmd+Shift+R"
