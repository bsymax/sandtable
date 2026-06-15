#!/bin/bash
# ============================================================================
# 品牌沙盘 M1 · 主工程京东云部署（server + web + database）
# 在服务器上以 root 执行：
#   bash sandtable-main-deploy.sh /root/sandtable-deploy.tar.gz
# ============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*"; }

TARBALL="${1:-}"
APP_DIR="/opt/sandtable"
APP_PORT=8000
WORKERS="${WORKERS:-4}"
DB_ROOT_PASS="${DB_ROOT_PASS:-}"
DB_APP_PASS="${DB_APP_PASS:-}"
CRED_FILE="/root/.sandtable-db-credentials"

if [[ -z "$TARBALL" || ! -f "$TARBALL" ]]; then
  err "用法: bash sandtable-main-deploy.sh /path/to/sandtable-deploy.tar.gz"
  exit 1
fi

# 重复部署：优先复用持久化密码（避免第二次随机密码连不上 MySQL）
if [[ -f "$CRED_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$CRED_FILE"
  info "已加载 ${CRED_FILE} 中的数据库密码"
elif [[ -f "$APP_DIR/DEPLOY-CREDENTIALS.txt" ]]; then
  DB_ROOT_PASS=$(grep -F 'MySQL root 密码:' "$APP_DIR/DEPLOY-CREDENTIALS.txt" | awk -F': ' '{print $2}')
  DB_APP_PASS=$(grep -F 'MySQL brand_app 密码:' "$APP_DIR/DEPLOY-CREDENTIALS.txt" | awk -F': ' '{print $2}')
  info "已从 ${APP_DIR}/DEPLOY-CREDENTIALS.txt 读取数据库密码"
fi

[[ -z "$DB_ROOT_PASS" ]] && DB_ROOT_PASS=$(openssl rand -base64 16 | tr -d '/+=' )
[[ -z "$DB_APP_PASS"  ]] && DB_APP_PASS=$(openssl rand -base64 12 | tr -d '/+=' )

mysql_root_ok() {
  mysql -u root -e "SELECT 1" &>/dev/null
}

mysql_root_pass_ok() {
  mysql -u root -p"${DB_ROOT_PASS}" -e "SELECT 1" &>/dev/null
}

mysql_recover_root() {
  warn "MySQL root 无法登录，执行一次性密码重置（仅本机 skip-grant-tables）..."
  systemctl stop mysql || true
  mkdir -p /var/run/mysqld
  chown mysql:mysql /var/run/mysqld 2>/dev/null || true
  mysqld --user=mysql --skip-grant-tables --skip-networking &
  local mpid=$!
  sleep 5
  mysql -u root <<SQL
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${DB_ROOT_PASS}';
FLUSH PRIVILEGES;
SQL
  kill "$mpid" 2>/dev/null || killall mysqld 2>/dev/null || true
  sleep 2
  systemctl start mysql
  sleep 3
  if ! mysql_root_pass_ok; then
    err "MySQL root 密码重置失败，请 SSH 登录服务器手动排查"
    exit 1
  fi
  info "MySQL root 密码已重置并写入 ${CRED_FILE}"
}

save_db_credentials() {
  cat > "$CRED_FILE" <<EOF
DB_ROOT_PASS='${DB_ROOT_PASS}'
DB_APP_PASS='${DB_APP_PASS}'
EOF
  chmod 600 "$CRED_FILE"
}

info "=============================================="
info "  品牌沙盘 M1 · 主工程部署"
info "=============================================="

# --- Step 1: 系统依赖 ---
info "Step 1/8: 安装系统依赖..."
export DEBIAN_FRONTEND=noninteractive
# 避免 apt 升级时重启 ssh.service 导致 SSH 断开、部署中断
export NEEDRESTART_MODE=l
if ! command -v nginx >/dev/null || ! command -v mysql >/dev/null; then
  apt-get update -qq
  apt-get install -y -qq -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" \
    python3 python3-pip python3-venv \
    mysql-server mysql-client nginx curl ufw git openssl rsync > /dev/null
  info "系统依赖安装完成"
else
  info "系统依赖已存在，跳过 apt-get（避免中断 SSH）"
fi

# --- Step 2: MySQL ---
info "Step 2/8: 配置 MySQL..."
systemctl start mysql
systemctl enable mysql

if mysql_root_ok; then
  mysql -u root <<SQL
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${DB_ROOT_PASS}';
FLUSH PRIVILEGES;
SQL
elif mysql_root_pass_ok; then
  info "MySQL root 已有密码，继续配置库与用户"
else
  mysql_recover_root
fi

mysql -u root -p"${DB_ROOT_PASS}" <<SQL
CREATE DATABASE IF NOT EXISTS brand_sandtable
  DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'brand_app'@'localhost' IDENTIFIED BY '${DB_APP_PASS}';
ALTER USER 'brand_app'@'localhost' IDENTIFIED BY '${DB_APP_PASS}';
GRANT ALL PRIVILEGES ON brand_sandtable.* TO 'brand_app'@'localhost';
FLUSH PRIVILEGES;
SQL

save_db_credentials

# 16G 机器：限制 MySQL 占用，给 FastAPI 留余量
cat > /etc/mysql/mysql.conf.d/99-sandtable.cnf <<'CNF'
[mysqld]
innodb_buffer_pool_size = 2G
max_connections = 100
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
CNF
systemctl restart mysql
info "MySQL 就绪（buffer_pool 2G）"

# --- Step 3: 解压项目 ---
info "Step 3/8: 解压项目到 ${APP_DIR}..."
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR"
# xattr 告警无害，静默即可
tar xzf "$TARBALL" -C "$APP_DIR" 2>/dev/null || tar xzf "$TARBALL" -C "$APP_DIR"

if [[ ! -f "$APP_DIR/server/main.py" ]]; then
  err "解压后找不到 ${APP_DIR}/server/main.py，请检查 tar 包结构"
  exit 1
fi

# Mac 打包可能保留 600 权限，Nginx(www-data) 会 403
chmod -R a+rX "$APP_DIR/web"
find "$APP_DIR/web" -type f -exec chmod 644 {} \;
find "$APP_DIR/web" -type d -exec chmod 755 {} \;

# --- Step 4: 前端 API 改为同源（Nginx 反代 /api） ---
info "Step 4/8: 前端改为生产模式（同源 API）..."
patch_api() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  # 统一去掉硬编码 API 地址，fetch 走同源 /api（避免 sed 特殊字符问题）
  sed -i 's|http://127.0.0.1:8000||g' "$f"
}
patch_api "$APP_DIR/web/profile.html"
patch_api "$APP_DIR/web/visit.html"
patch_api "$APP_DIR/web/intel.html"
patch_api "$APP_DIR/web/js/api.js"

# --- Step 5: Python 虚拟环境 ---
info "Step 5/8: 安装 Python 依赖..."
cd "$APP_DIR/server"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

PUBLIC_IP=$(curl -s --max-time 5 ifconfig.me 2>/dev/null || curl -s --max-time 5 icanhazip.com 2>/dev/null || echo "127.0.0.1")

cat > "$APP_DIR/server/.env" <<EOF
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=brand_app
DB_PASSWORD=${DB_APP_PASS}
DB_NAME=brand_sandtable
DB_CHARSET=utf8mb4

SERVER_HOST=127.0.0.1
SERVER_PORT=${APP_PORT}

CORS_ORIGINS=http://${PUBLIC_IP},http://127.0.0.1
EOF
chmod 600 "$APP_DIR/server/.env"

# --- Step 6: 初始化数据库 ---
info "Step 6/8: 导入 schema.sql..."
mysql -u brand_app -p"${DB_APP_PASS}" brand_sandtable \
  < "$APP_DIR/database/schema.sql" 2>/dev/null || {
  warn "schema 导入有警告，尝试 ORM 补表..."
}
cd "$APP_DIR/server"
source venv/bin/activate
python3 -c "
from database import engine
from models import Base
Base.metadata.create_all(bind=engine)
print('ORM sync OK')
"

# --- Step 7: systemd + Nginx ---
info "Step 7/8: 配置 systemd 与 Nginx..."

cat > /etc/systemd/system/sandtable.service <<EOF
[Unit]
Description=品牌沙盘 M1 FastAPI（主工程）
After=network.target mysql.service
Wants=mysql.service

[Service]
User=root
WorkingDirectory=${APP_DIR}/server
EnvironmentFile=${APP_DIR}/server/.env
ExecStart=${APP_DIR}/server/venv/bin/uvicorn main:app --host 127.0.0.1 --port ${APP_PORT} --workers ${WORKERS}
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable sandtable.service
systemctl restart sandtable.service

cat > /etc/nginx/sites-available/sandtable <<NGINX
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 16m;

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    location /api/ {
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
    }

    location /docs {
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_set_header Host \$host;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_set_header Host \$host;
    }

    location / {
        root ${APP_DIR}/web;
        index index.html;
        try_files \$uri \$uri/ =404;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/sandtable /etc/nginx/sites-enabled/sandtable
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

# --- Step 8: 防火墙 ---
info "Step 8/8: 防火墙..."
ufw allow 22/tcp > /dev/null 2>&1 || true
ufw allow 80/tcp > /dev/null 2>&1 || true
ufw allow 443/tcp > /dev/null 2>&1 || true
echo "y" | ufw enable > /dev/null 2>&1 || true

# 保存凭据（勿外传）
cat > "$APP_DIR/DEPLOY-CREDENTIALS.txt" <<EOF
部署时间: $(date '+%Y-%m-%d %H:%M:%S')
公网 IP: ${PUBLIC_IP}
MySQL root 密码: ${DB_ROOT_PASS}
MySQL brand_app 密码: ${DB_APP_PASS}
项目目录: ${APP_DIR}
EOF
chmod 600 "$APP_DIR/DEPLOY-CREDENTIALS.txt"
save_db_credentials

# --- 冒烟 ---
sleep 2
info "冒烟测试..."
BRANDS=$(curl -s --max-time 10 "http://127.0.0.1/api/brands" | head -c 120)
info "/api/brands: ${BRANDS}..."

echo ""
info "=============================================="
info "  ✅ 部署完成"
info "=============================================="
echo ""
info "工作台:   http://${PUBLIC_IP}/"
info "品牌档案: http://${PUBLIC_IP}/profile.html"
info "拜访助手: http://${PUBLIC_IP}/visit.html"
info "情报流:   http://${PUBLIC_IP}/intel.html"
info "API 文档: http://${PUBLIC_IP}/docs"
echo ""
info "凭据文件: ${APP_DIR}/DEPLOY-CREDENTIALS.txt （仅服务器本机，勿发到群里）"
info "服务管理: systemctl status|restart sandtable"
info "日志:     journalctl -u sandtable -f"
echo ""
