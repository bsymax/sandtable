#!/bin/bash
# 502 热修：M2 intel CSV 上传依赖 python-multipart，缺则后端无法启动
# 用法: bash deploy/point-deploy-fix-502-multipart.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 修复 502 @ ${IP}：安装 python-multipart 并重启 sandtable"

scp "${SSH_OPTS[@]}" "$ROOT/server/requirements.txt" "root@${IP}:/opt/sandtable/server/"

ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
cd /opt/sandtable/server
source venv/bin/activate
pip install -q 'python-multipart>=0.0.6'
systemctl restart sandtable
sleep 3
systemctl is-active sandtable
curl -s -o /dev/null -w "brands HTTP %{http_code}\n" http://127.0.0.1:8000/api/brands
REMOTE

bash "$ROOT/deploy/smoke-test.sh" "http://${IP}"
echo "✅ 若 brands OK，外网 Cmd+Shift+R 硬刷新"
