#!/bin/bash
# ============================================================================
# 品牌沙盘 M1 · 智能拜访助手 — 京东云一键部署脚本
# 适用系统: Ubuntu 22.04 / CentOS 7+
# 使用方式: chmod +x deploy.sh && sudo bash deploy.sh
# ============================================================================

set -e

# -------------------- 颜色输出 --------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*"; }

# -------------------- 用户可配置项 --------------------
# 数据库密码（脚本自动生成或留空则随机生成）
DB_ROOT_PASS="${DB_ROOT_PASS:-}"
DB_APP_PASS="${DB_APP_PASS:-}"

# 部署目录
APP_DIR="/opt/brand-sandtable"

# 服务端口
APP_PORT=8000

# 域名（留空则跳过 HTTPS，仅 HTTP）
DOMAIN="${DOMAIN:-}"

info "=============================================="
info "  品牌沙盘 M1 · 一键部署开始"
info "=============================================="

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
        mysql-server mysql-client nginx certbot python3-certbot-nginx \
        curl ufw git > /dev/null 2>&1
elif [ -f /etc/redhat-release ]; then
    OS="redhat"
    info "检测到 RHEL/CentOS 系统"
    yum install -y epel-release > /dev/null 2>&1
    yum install -y python3 python3-pip python3-virtualenv \
        mysql-server nginx certbot python3-certbot-nginx \
        curl firewalld git > /dev/null 2>&1
else
    err "不支持的系统，请使用 Ubuntu 22.04 或 CentOS 7+"
    exit 1
fi

info "系统依赖安装完成"

# ====================================================================
# Step 2 — MySQL 安装与初始化
# ====================================================================
info "Step 2/7: 配置 MySQL 数据库..."

# 启动 MySQL
if [ "$OS" = "debian" ]; then
    systemctl start mysql
    systemctl enable mysql
elif [ "$OS" = "redhat" ]; then
    systemctl start mysqld
    systemctl enable mysqld
fi

# 生成或使用提供的密码
if [ -z "$DB_ROOT_PASS" ]; then
    DB_ROOT_PASS=$(openssl rand -base64 16 | tr -d '/+=')
    info "已生成 MySQL root 密码: ${DB_ROOT_PASS}  (请妥善保存!)"
fi
if [ -z "$DB_APP_PASS" ]; then
    DB_APP_PASS=$(openssl rand -base64 12 | tr -d '/+=')
    info "已生成应用数据库密码: ${DB_APP_PASS}"
fi

# 如果 root 使用 auth_socket 认证（Ubuntu），需要先切换到 mysql_native_password
if [ "$OS" = "debian" ]; then
    # Ubuntu 22.04 默认 root 通过 auth_socket 登录，无需密码
    mysql -u root <<SQL 2>/dev/null || true
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${DB_ROOT_PASS}';
FLUSH PRIVILEGES;
SQL
fi

# 创建应用数据库和用户
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
# Step 3 — 部署应用代码
# ====================================================================
info "Step 3/7: 部署应用代码..."

# 检测代码源位置（优先用当前目录下的项目，其次用 WORKSPACE 传入的路径）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_SRC="${SCRIPT_DIR}"

# 如果脚本同级有 backend/frontend/database 目录，说明项目源码在一起
if [ ! -d "$PROJECT_SRC/backend" ] && [ -n "$WORKSPACE" ]; then
    PROJECT_SRC="$WORKSPACE"
fi

if [ ! -d "$PROJECT_SRC/backend" ]; then
    err "找不到项目源码！请将部署脚本与 peixiao-m1-0612 目录放在一起，或设置 WORKSPACE 变量。"
    err "当前搜索路径: $PROJECT_SRC"
    exit 1
fi

# 清理旧目录
rm -rf "$APP_DIR"

# 复制项目文件
cp -r "$PROJECT_SRC" "$APP_DIR"
info "项目代码已复制到 $APP_DIR"

# ====================================================================
# Step 4 — 修复前端 API 地址（生产环境用相对路径）
# ====================================================================
info "Step 4/7: 配置前端连接地址..."

# 修改 api.js：生产环境使用空字符串（同源），Nginx 反代会处理 /api/ 路由
if [ -f "$APP_DIR/frontend/api.js" ]; then
    # 将 127.0.0.1:8000 替换为空（相对路径）
    sed -i "s|http://127.0.0.1:8000||g" "$APP_DIR/frontend/api.js"
    info "api.js 已更新为生产模式（相对路径）"
fi

# ====================================================================
# Step 5 — 安装 Python 依赖 & 配置后端
# ====================================================================
info "Step 5/7: 安装 Python 依赖..."

cd "$APP_DIR/backend"

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# 写入 .env 生产配置
cat > .env <<EOF
# 数据库配置（生产环境）
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=brand_app
DB_PASSWORD=${DB_APP_PASS}
DB_NAME=brand_sandtable
DB_CHARSET=utf8mb4

# 服务配置
SERVER_HOST=0.0.0.0
SERVER_PORT=${APP_PORT}

# CORS 允许的前端地址（部署后同域，相对路径无需 CORS，但仍保留安全配置）
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:5500,http://localhost:5500
EOF

info "Python 依赖安装完成，.env 已生成"

# ====================================================================
# Step 6 — 初始化数据库表结构 & 种子数据
# ====================================================================
info "Step 6/7: 初始化数据库..."

# 导入 schema.sql
mysql -u brand_app -p"${DB_APP_PASS}" brand_sandtable < "$APP_DIR/database/schema.sql" 2>/dev/null
# 如果表已有数据，容错处理
if [ $? -ne 0 ]; then
    warn "schema 导入有警告（可能表已存在），尝试继续..."
    mysql -u brand_app -p"${DB_APP_PASS}" brand_sandtable < "$APP_DIR/database/schema.sql" 2>/dev/null || true
fi

# SQLAlchemy 自动补建缺失的表
python -c "
from database import engine
from models import Base
Base.metadata.create_all(bind=engine)
print('ORM 表结构同步完成')
"

info "数据库初始化完成"

# ====================================================================
# Step 7 — systemd 服务 & Nginx & 防火墙
# ====================================================================
info "Step 7/7: 配置进程守护 & 反向代理..."

# --- systemd 服务 ---
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

info "systemd 服务已配置并启动"

# --- Nginx 配置 ---
cat > /etc/nginx/sites-available/brand-sandtable <<'NGINX'
server {
    listen 80;
    # 如果有域名，取消注释下面两行并替换 your-domain.com
    # server_name your-domain.com;
    # return 301 https://$host$request_uri;

    # API 反代到 FastAPI
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    # 前端静态文件
    root /opt/brand-sandtable/frontend;
    index visit_assistant_api.html index.html;

    # 主页 / → 拜访助手
    location = / {
        try_files /visit_assistant_api.html =404;
    }

    # 静态文件直接服务
    location / {
        try_files $uri $uri/ =404;
    }
}
NGINX

# 启用站点
if [ -d /etc/nginx/sites-enabled ]; then
    ln -sf /etc/nginx/sites-available/brand-sandtable /etc/nginx/sites-enabled/brand-sandtable
    # 删除默认站点
    rm -f /etc/nginx/sites-enabled/default
elif [ -d /etc/nginx/conf.d ]; then
    # CentOS 风格
    ln -sf /etc/nginx/sites-available/brand-sandtable /etc/nginx/conf.d/brand-sandtable.conf
fi

nginx -t && systemctl reload nginx
info "Nginx 配置完成"

# --- 防火墙 ---
if command -v ufw > /dev/null; then
    ufw allow 80/tcp > /dev/null 2>&1 || true
    ufw allow 443/tcp > /dev/null 2>&1 || true
    ufw allow 22/tcp > /dev/null 2>&1 || true
    ufw --force enable > /dev/null 2>&1 || true
    info "UFW 防火墙已配置"
elif command -v firewall-cmd > /dev/null; then
    firewall-cmd --permanent --add-service=http > /dev/null 2>&1 || true
    firewall-cmd --permanent --add-service=https > /dev/null 2>&1 || true
    firewall-cmd --reload > /dev/null 2>&1 || true
    info "firewalld 防火墙已配置"
fi

# ====================================================================
# 部署完成
# ====================================================================
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "服务器IP")

echo ""
info "=============================================="
info "  ✅ 品牌沙盘 M1 部署完成！"
info "=============================================="
echo ""
info "访问地址:    http://${SERVER_IP}"
info "API 文档:    http://${SERVER_IP}/docs"
echo ""
info "数据库 root 密码: ${DB_ROOT_PASS}"
info "数据库 app  密码: ${DB_APP_PASS}"
info "（已保存至 ${APP_DIR}/backend/.env）"
echo ""
if [ -z "$DOMAIN" ]; then
    warn "未配置域名，当前仅支持 HTTP 访问。"
    warn "如需 HTTPS，请："
    warn "  1. 在 Nginx 中配置 server_name 为你的域名"
    warn "  2. 运行: certbot --nginx -d your-domain.com"
fi
echo ""
info "服务管理命令:"
info "  systemctl status brand-sandtable   # 查看状态"
info "  systemctl restart brand-sandtable  # 重启服务"
info "  journalctl -u brand-sandtable -f   # 查看日志"
echo ""
