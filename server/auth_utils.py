"""M3/M5 登录：密码哈希与会话 token"""

import hashlib
import re
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Tuple

from config import AUTH_SALT, SESSION_TTL_HOURS

try:
    import bcrypt
except ImportError:  # pragma: no cover
    bcrypt = None  # type: ignore


def hash_password_sha256(password: str) -> str:
    raw = f"{AUTH_SALT}:{password}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def hash_password(password: str) -> Tuple[str, str]:
    """新密码一律 bcrypt；返回 (hash, algo)。"""
    if bcrypt is None:
        raise RuntimeError("bcrypt 未安装，请 pip install bcrypt")
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    return hashed, "bcrypt"


def verify_password(password: str, password_hash: str, algo: str = "sha256") -> bool:
    if algo == "bcrypt":
        if bcrypt is None:
            return False
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except ValueError:
            return False
    return hash_password_sha256(password) == password_hash


def validate_new_password(username: str, password: str) -> Optional[str]:
    if len(password) < 8:
        return "密码至少 8 位"
    if password.lower() == username.lower():
        return "密码不可与用户名相同"
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return "密码须同时包含字母和数字"
    return None


def generate_temp_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        if re.search(r"[A-Za-z]", pwd) and re.search(r"\d", pwd):
            return pwd


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def session_expires_at() -> datetime:
    return datetime.utcnow() + timedelta(hours=SESSION_TTL_HOURS)
