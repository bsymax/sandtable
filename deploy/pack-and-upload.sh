#!/bin/bash
# ============================================================================
# 在本机 Mac 执行：打包主工程并上传到京东云，远程一键部署
#
# 用法:
#   bash deploy/pack-and-upload.sh <公网IP>
#
# 会提示输入 root SSH 密码（请勿把密码发给 AI/群里）
#
# 说明：远程部署用 nohup 后台跑，避免 apt 重启 ssh 导致连接断开。
# ============================================================================
set -euo pipefail

IP="${1:-}"
if [[ -z "$IP" ]]; then
  echo "用法: bash deploy/pack-and-upload.sh <公网IP>"
  echo "示例: bash deploy/pack-and-upload.sh 123.56.78.90"
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="/tmp/sandtable-deploy-$$.tar.gz"
SSH_OPTS=(-o ConnectTimeout=30 -o ServerAliveInterval=30 -o ServerAliveCountMax=60)

echo "==> 打包主工程..."
export COPYFILE_DISABLE=1
BUNDLE="/tmp/sandtable-bundle-$$"
mkdir -p "$BUNDLE"
rsync -a \
  --exclude='.env' --exclude='__pycache__' --exclude='*.pyc' \
  "$ROOT/server" "$ROOT/web" "$ROOT/database" "$BUNDLE/"
# 清 macOS 扩展属性，避免 Linux tar 刷屏
xattr -cr "$BUNDLE" 2>/dev/null || true
COPYFILE_DISABLE=1 tar czf "$TMP" -C "$BUNDLE" .
rm -rf "$BUNDLE"

echo "==> 上传至 root@${IP} ..."
scp "${SSH_OPTS[@]}" "$TMP" "root@${IP}:/root/sandtable-deploy.tar.gz"
scp "${SSH_OPTS[@]}" "$ROOT/deploy/sandtable-main-deploy.sh" "root@${IP}:/root/"

echo "==> 远程后台部署（SSH 断开也会继续，约 5～10 分钟）..."
ssh "${SSH_OPTS[@]}" "root@${IP}" \
  "chmod +x /root/sandtable-main-deploy.sh && nohup bash /root/sandtable-main-deploy.sh /root/sandtable-deploy.tar.gz > /root/sandtable-deploy.log 2>&1 & echo \$! > /root/sandtable-deploy.pid && echo DEPLOY_STARTED"

rm -f "$TMP"

echo "==> 等待服务就绪（本机轮询 HTTP，无需再输密码）..."
OK=0
for i in $(seq 1 40); do
  sleep 15
  CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 8 "http://${IP}/api/brands" 2>/dev/null || echo "000")
  if [[ "$CODE" == "200" ]]; then
    OK=1
    break
  fi
  echo "   ... ${i}/40（$((i * 15))s）API HTTP ${CODE}"
done

echo ""
if [[ "$OK" == "1" ]]; then
  echo "✅ 部署成功"
  echo "   工作台: http://${IP}/"
  echo "   档案:   http://${IP}/profile.html"
  echo "   拜访:   http://${IP}/visit.html"
  echo "   情报:   http://${IP}/intel.html"
  bash "$ROOT/deploy/smoke-test.sh" "http://${IP}" || true
else
  echo "⚠️  超时未检测到 /api/brands。请 SSH 登录查看日志："
  echo "   ssh root@${IP}"
  echo "   tail -50 /root/sandtable-deploy.log"
  exit 1
fi
