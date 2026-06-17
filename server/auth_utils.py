"""M3 登录：密码哈希与会话 token"""

import hashlib
import secrets
from datetime import datetime, timedelta

from config import AUTH_SALT, SESSION_TTL_HOURS


def hash_password(password: str) -> str:
    raw = f"{AUTH_SALT}:{password}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def session_expires_at() -> datetime:
    return datetime.utcnow() + timedelta(hours=SESSION_TTL_HOURS)
