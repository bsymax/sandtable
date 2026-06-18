"""
数据库连接配置 & 应用设置
"""

import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

DB_HOST     = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT     = int(os.getenv("DB_PORT", "3306"))
DB_USER     = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME     = os.getenv("DB_NAME", "brand_sandtable")
DB_CHARSET  = os.getenv("DB_CHARSET", "utf8mb4")

SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

CORS_ORIGINS = [
    o.strip() for o in
    os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:5500").split(",")
    if o.strip()
]

# ---------- M3 登录 / LLM ----------
AUTH_SECRET = os.getenv("AUTH_SECRET", "sandtable-m3-dev-change-me")
AUTH_SALT = os.getenv("AUTH_SALT", "sandtable-auth-salt")
SESSION_TTL_HOURS = int(os.getenv("SESSION_TTL_HOURS", "72"))
# false = M2 兼容（未登录仍可看全量）；true = 必须登录
AUTH_REQUIRED = os.getenv("AUTH_REQUIRED", "false").lower() in ("1", "true", "yes")
LLM_ENABLED = os.getenv("LLM_ENABLED", "false").lower() in ("1", "true", "yes")
LLM_GATEWAY_URL = os.getenv("LLM_GATEWAY_URL", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
LLM_TIMEOUT_SEC = float(os.getenv("LLM_TIMEOUT_SEC", "25"))
# M4-B 配额（0 = 不限制）
LLM_DAILY_CAP = int(os.getenv("LLM_DAILY_CAP", "2000"))
LLM_USER_DAILY_CAP = int(os.getenv("LLM_USER_DAILY_CAP", "60"))
LLM_READONLY_ENABLED = os.getenv("LLM_READONLY_ENABLED", "false").lower() in ("1", "true", "yes")
# M4-C 数仓质量规则
DW_QUALITY_STRICT = os.getenv("DW_QUALITY_STRICT", "true").lower() in ("1", "true", "yes")
# M4-C 经营指标主频（BI 首接为 monthly；档案/拜访「数据截至」读此类型）
DW_METRICS_PERIOD_TYPE = os.getenv("DW_METRICS_PERIOD_TYPE", "monthly").strip().lower()
if DW_METRICS_PERIOD_TYPE not in ("weekly", "monthly"):
    DW_METRICS_PERIOD_TYPE = "monthly"

# SQLAlchemy 连接字符串（同步 + PyMySQL）
DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    f"?charset={DB_CHARSET}"
)
