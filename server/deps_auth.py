"""M3 鉴权依赖：可选/必选当前用户、品牌范围"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Set

from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session

from config import AUTH_REQUIRED
from database import get_db
from models import Brand, User, UserSession


@dataclass
class AuthUser:
    id: int
    username: str
    display_name: str
    role: str
    brand_ids: Set[int]
    brand_keys: Set[str]

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    def can_access_brand_id(self, brand_id: Optional[int]) -> bool:
        if brand_id is None:
            return True
        if self.is_admin:
            return True
        return brand_id in self.brand_ids

    def can_access_name_key(self, name_key: Optional[str]) -> bool:
        if not name_key:
            return True
        if self.is_admin:
            return True
        return name_key in self.brand_keys


def _load_user_from_token(db: Session, token: str) -> Optional[AuthUser]:
    if not token:
        return None
    sess = db.query(UserSession).filter(UserSession.token == token).first()
    if not sess or sess.expires_at < datetime.utcnow():
        return None
    user = db.query(User).filter(User.id == sess.user_id, User.is_active == True).first()
    if not user:
        return None
    brand_ids = {ub.brand_id for ub in (user.brands or [])}
    brand_keys: Set[str] = set()
    if brand_ids:
        for b in db.query(Brand).filter(Brand.id.in_(brand_ids)).all():
            brand_keys.add(b.name_key)
    return AuthUser(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=user.role,
        brand_ids=brand_ids,
        brand_keys=brand_keys,
    )


def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Optional[AuthUser]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:].strip()
    return _load_user_from_token(db, token)


def get_current_user(
    user: Optional[AuthUser] = Depends(get_current_user_optional),
) -> AuthUser:
    if user:
        return user
    if AUTH_REQUIRED:
        raise HTTPException(401, "请先登录")
    raise HTTPException(401, "未登录")


def require_brand_id(user: Optional[AuthUser], brand_id: Optional[int]) -> None:
    if not user:
        return
    if not user.can_access_brand_id(brand_id):
        raise HTTPException(403, "无权访问该品牌")


def require_name_key(user: Optional[AuthUser], name_key: str) -> None:
    if not user:
        return
    if not user.can_access_name_key(name_key):
        raise HTTPException(403, "无权访问该品牌")


def filter_brand_query(q, user: Optional[AuthUser]):
    if not user or user.is_admin:
        return q
    if not user.brand_ids:
        return q.filter(Brand.id == -1)
    return q.filter(Brand.id.in_(user.brand_ids))


def filter_by_brand_ids(q, brand_id_column, user: Optional[AuthUser]):
    """按 user_brands 过滤任意带 brand_id 列的查询"""
    if not user or user.is_admin:
        return q
    if not user.brand_ids:
        return q.filter(brand_id_column == -1)
    return q.filter(brand_id_column.in_(user.brand_ids))
