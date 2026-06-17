#!/bin/bash
# 外网 502 / 登录失败 · 诊断并重启后端
# 用法: bash deploy/point-fix-502-restart.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 外网探测（修复前）..."
curl -s -o /dev/null -w "  /api/health → HTTP %{http_code}\n" "http://${IP}/api/health" || true
curl -s -o /dev/null -w "  /api/auth/login → HTTP %{http_code}\n" -X POST "http://${IP}/api/auth/login" \
  -H 'Content-Type: application/json' -d '{"username":"admin","password":"sand123"}' || true

echo ""
echo "==> SSH 诊断 + 修复 root@${IP}..."
ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
APP=/opt/sandtable

echo "--- systemctl status ---"
systemctl is-active sandtable || true
systemctl status sandtable --no-pager -l | tail -15 || true

echo ""
echo "--- 最近日志 ---"
journalctl -u sandtable -n 25 --no-pager || true

echo ""
echo "--- 依赖 + 重启 ---"
cd "$APP/server"
source venv/bin/activate
pip install -q -r requirements.txt
python3 -c "from main import app; print('import OK')"

systemctl restart sandtable
sleep 4
systemctl is-active sandtable

echo ""
echo "--- 本机 API ---"
curl -s -o /dev/null -w "health %{http_code}\n" http://127.0.0.1:8000/api/health
curl -s -o /dev/null -w "login %{http_code}\n" -X POST http://127.0.0.1:8000/api/auth/login \
  -H 'Content-Type: application/json' -d '{"username":"zhou","password":"sand123"}'
REMOTE

echo ""
echo "==> 外网复测..."
bash "$ROOT/deploy/smoke-test.sh" "http://${IP}" || true
curl -s -X POST "http://${IP}/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"username":"zhou","password":"sand123"}' | python3 -c "
import sys,json
d=json.load(sys.stdin)
assert d.get('token'), d
print('  登录 OK:', d.get('username'), '品牌数', len(d.get('brands',[])))
"
echo ""
echo "✅ 后端恢复。请三人硬刷新 http://${IP}/login.html 重试"
