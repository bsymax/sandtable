#!/bin/bash
# ============================================================================
# 品牌沙盘 M1 · 京东云一键部署（自解压单文件版）
#
# 使用: sudo bash deploy-onefile.sh
# 只需要这一个文件，上传到服务器后以 root 执行即可
# ============================================================================
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*"; }

# === 用户配置（可改） ===
DB_ROOT_PASS="${DB_ROOT_PASS:-}"
DB_APP_PASS="${DB_APP_PASS:-}"
APP_DIR="/opt/brand-sandtable"
APP_PORT=8000
# 如果你的域名是 brand.example.com，改这里：
DOMAIN="${DOMAIN:-}"

info "=============================================="
info "  品牌沙盘 M1 · 自解压部署包"
info "=============================================="

# ====================================================================
# Step 0 — 自解压源代码（base64 嵌入在文件末尾）
# ====================================================================
info "Step 0/7: 解压项目源码..."
WORK_DIR="/tmp/brand-sandtable-deploy-$$"
mkdir -p "$WORK_DIR"
ARCHIVE_LINE=$(awk '/^__ARCHIVE_BELOW__/ {print NR+1; exit}' "$0")
tail -n +"$ARCHIVE_LINE" "$0" | base64 -d | tar xz -C "$WORK_DIR"
info "源码已解压到 $WORK_DIR"

cd "$WORK_DIR"

# ====================================================================
# Step 1 — 系统环境检测 & 依赖安装
# ====================================================================
info "Step 1/7: 安装系统依赖..."

if [ -f /etc/debian_version ]; then
    OS="debian"
    info "检测到 Debian/Ubuntu 系统"
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq python3 python3-pip python3-venv \
        mysql-server mysql-client nginx \
        curl ufw git openssl > /dev/null 2>&1
elif [ -f /etc/redhat-release ]; then
    OS="redhat"
    info "检测到 RHEL/CentOS 系统"
    yum install -y epel-release > /dev/null 2>&1
    yum install -y python3 python3-pip python3-virtualenv \
        mysql-server nginx \
        curl firewalld git openssl > /dev/null 2>&1
else
    err "不支持的系统，请使用 Ubuntu 22.04 或 CentOS 7+"
    exit 1
fi
info "系统依赖安装完成"

# ====================================================================
# Step 2 — MySQL 安装与初始化
# ====================================================================
info "Step 2/7: 配置 MySQL 数据库..."

if [ "$OS" = "debian" ]; then
    systemctl start mysql
    systemctl enable mysql
elif [ "$OS" = "redhat" ]; then
    systemctl start mysqld
    systemctl enable mysqld
fi

[ -z "$DB_ROOT_PASS" ] && DB_ROOT_PASS=$(openssl rand -base64 16 | tr -d '/+=')
[ -z "$DB_APP_PASS" ]  && DB_APP_PASS=$(openssl rand -base64 12 | tr -d '/+=')

info "MySQL root 密码: ${DB_ROOT_PASS}"
info "应用数据库密码: ${DB_APP_PASS}"

# Ubuntu: root 默认用 auth_socket，需要改为密码认证
if [ "$OS" = "debian" ]; then
    mysql -u root <<SQL 2>/dev/null || true
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${DB_ROOT_PASS}';
FLUSH PRIVILEGES;
SQL
fi

mysql -u root -p"${DB_ROOT_PASS}" 2>/dev/null <<SQL || mysql -u root <<SQL
CREATE DATABASE IF NOT EXISTS brand_sandtable
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'brand_app'@'localhost' IDENTIFIED BY '${DB_APP_PASS}';
GRANT ALL PRIVILEGES ON brand_sandtable.* TO 'brand_app'@'localhost';
FLUSH PRIVILEGES;
SQL
info "MySQL 配置完成"

# ====================================================================
# Step 3 — 部署应用代码 & 初始化数据库
# ====================================================================
info "Step 3/7: 部署应用代码..."
rm -rf "$APP_DIR"

# 找到解压后的项目目录（peixiao-m1-0612）
SRC_DIR=$(find "$WORK_DIR" -name "main.py" -path "*/backend/*" | head -1 | xargs dirname | xargs dirname)
if [ -z "$SRC_DIR" ]; then
    err "找不到项目源码！"
    exit 1
fi
cp -r "$SRC_DIR" "$APP_DIR"
info "项目代码已部署到 $APP_DIR"

# 修复前端 API 地址为生产模式
info "Step 4/7: 配置前端..."
sed -i "s|http://127.0.0.1:8000||g" "$APP_DIR/frontend/api.js" 2>/dev/null || true

# ====================================================================
# Step 5 — Python 环境
# ====================================================================
info "Step 5/7: 安装 Python 依赖..."
cd "$APP_DIR/backend"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

cat > .env <<EOF
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=brand_app
DB_PASSWORD=${DB_APP_PASS}
DB_NAME=brand_sandtable
DB_CHARSET=utf8mb4
SERVER_HOST=0.0.0.0
SERVER_PORT=${APP_PORT}
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:5500,http://localhost:5500
EOF
info ".env 已生成"

# ====================================================================
# Step 6 — 数据库初始化
# ====================================================================
info "Step 6/7: 初始化数据库表..."
mysql -u brand_app -p"${DB_APP_PASS}" brand_sandtable < "$APP_DIR/database/schema.sql" 2>/dev/null || true
# SQLAlchemy 补建缺表
python -c "
from database import engine
from models import Base
Base.metadata.create_all(bind=engine)
" 2>/dev/null || true
info "数据库初始化完成"

# ====================================================================
# Step 7 — systemd + Nginx + 启动
# ====================================================================
info "Step 7/7: 配置服务守护 & Nginx 反向代理..."

cat > /etc/systemd/system/brand-sandtable.service <<EOF
[Unit]
Description=品牌沙盘 M1 FastAPI 服务
After=network.target mysql.service mysqld.service
Wants=mysql.service

[Service]
User=root
WorkingDirectory=${APP_DIR}/backend
ExecStart=${APP_DIR}/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port ${APP_PORT} --workers 2
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable brand-sandtable.service
systemctl restart brand-sandtable.service
info "systemd 服务已启动"

# Nginx
cat > /etc/nginx/sites-available/brand-sandtable <<'NGINXCONF'
server {
    listen 80;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    root /opt/brand-sandtable/frontend;
    index visit_assistant_api.html index.html;

    location = / {
        try_files /visit_assistant_api.html =404;
    }

    location / {
        try_files $uri $uri/ =404;
    }
}
NGINXCONF

if [ -d /etc/nginx/sites-enabled ]; then
    ln -sf /etc/nginx/sites-available/brand-sandtable /etc/nginx/sites-enabled/brand-sandtable
    rm -f /etc/nginx/sites-enabled/default
elif [ -d /etc/nginx/conf.d ]; then
    ln -sf /etc/nginx/sites-available/brand-sandtable /etc/nginx/conf.d/brand-sandtable.conf
fi

nginx -t && systemctl reload nginx
info "Nginx 配置完成"

# 防火墙
if command -v ufw > /dev/null; then
    ufw allow 80/tcp > /dev/null 2>&1 || true
    ufw allow 22/tcp > /dev/null 2>&1 || true
    ufw --force enable > /dev/null 2>&1 || true
elif command -v firewall-cmd > /dev/null; then
    firewall-cmd --permanent --add-service=http > /dev/null 2>&1 || true
    firewall-cmd --reload > /dev/null 2>&1 || true
fi

# 京东云安全组提示
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "服务器IP")

echo ""
info "=============================================="
info "  ✅ 品牌沙盘 M1 部署完成！"
info "=============================================="
echo ""
info "访问地址:    http://${SERVER_IP}"
info "API 文档:    http://${SERVER_IP}/docs"
echo ""
info "数据库密码已保存至: ${APP_DIR}/backend/.env"
echo ""
warn "⚠️  京东云轻量云主机默认有安全组/防火墙，请确保在京东云控制台开放 80 端口！"
warn "   操作路径: 控制台 → 轻量云主机 → 实例详情 → 防火墙 → 添加规则 → TCP 80"
echo ""
info "服务管理:"
info "  systemctl status brand-sandtable"
info "  journalctl -u brand-sandtable -f"
echo ""

# 清理
rm -rf "$WORK_DIR"
exit 0

# ⬇⬇⬇ 源代码包（base64 编码）⬇⬇⬇ 不要删除此行
__ARCHIVE_BELOW__
