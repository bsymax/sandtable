#!/bin/bash
# 开开 M5 首包 kaikai-m5-0622-pilot · intel + index + 名单/FAQ 模板
# 用法: bash deploy/point-deploy-kaikai-m5-0622.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 开开 M5 合并上云 → root@${IP}"

scp "${SSH_OPTS[@]}" \
  "$ROOT/web/intel.html" \
  "$ROOT/web/index.html" \
  "root@${IP}:/opt/sandtable/web/"

scp "${SSH_OPTS[@]}" \
  "$ROOT/docs/templates/pilot-faq-intel.md" \
  "$ROOT/docs/templates/pilot-spotcheck.md" \
  "$ROOT/docs/templates/pilot-users-changelog.md" \
  "$ROOT/docs/templates/pilot-users-v1.example.csv" \
  "root@${IP}:/opt/sandtable/docs/templates/" 2>/dev/null || {
  ssh "${SSH_OPTS[@]}" "root@${IP}" 'mkdir -p /opt/sandtable/docs/templates'
  scp "${SSH_OPTS[@]}" \
    "$ROOT/docs/templates/pilot-faq-intel.md" \
    "$ROOT/docs/templates/pilot-spotcheck.md" \
    "$ROOT/docs/templates/pilot-users-changelog.md" \
    "$ROOT/docs/templates/pilot-users-v1.example.csv" \
    "root@${IP}:/opt/sandtable/docs/templates/"
}

ssh "${SSH_OPTS[@]}" "root@${IP}" 'chmod -R a+rX /opt/sandtable/web /opt/sandtable/docs/templates 2>/dev/null || chmod -R a+rX /opt/sandtable/web'

echo "==> 外网抽查 intel title..."
curl -s http://${IP}/intel.html | rg -q '品牌情报流 · 品牌沙盘' && echo "OK intel title" || echo "WARN: 请硬刷新验收"

echo "✅ 完成。验收:"
echo "   http://${IP}/intel.html"
echo "   http://${IP}/"
echo "   硬刷新 Cmd+Shift+R"
