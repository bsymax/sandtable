"""
M3 登录路由
"""

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from auth_utils import new_session_token, session_expires_at, verify_password
from database import get_db
from deps_auth import AuthUser, get_current_user_optional
from models import Brand, User, UserSession
from schemas import LoginIn, LoginOut, MeOut, UserBrandOut

router = APIRouter()


def _user_brands_out(db: Session, user: User) -> list:
    if user.role == "admin":
        brands = db.query(Brand).filter(Brand.status == "active").order_by(Brand.id).all()
    else:
        ids = [ub.brand_id for ub in (user.brands or [])]
        brands = (
            db.query(Brand).filter(Brand.id.in_(ids), Brand.status == "active").order_by(Brand.id).all()
            if ids else []
        )
    return [UserBrandOut(id=b.id, name=b.name, name_key=b.name_key, level=b.level) for b in brands]


@router.post("/api/auth/login", response_model=LoginOut, tags=["登录"])
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username, User.is_active == True).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "用户名或密码错误")
    token = new_session_token()
    db.add(UserSession(user_id=user.id, token=token, expires_at=session_expires_at()))
    db.commit()
    return LoginOut(
        token=token,
        user_id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=user.role,
        brands=_user_brands_out(db, user),
    )


@router.post("/api/auth/logout", tags=["登录"])
def logout(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        db.query(UserSession).filter(UserSession.token == token).delete()
        db.commit()
    return {"message": "已退出"}


@router.get("/api/auth/me", response_model=MeOut, tags=["登录"])
def me(
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    if not user:
        raise HTTPException(401, "未登录")
    db_user = db.query(User).filter(User.id == user.id).first()
    if not db_user:
        raise HTTPException(401, "用户不存在")
    return MeOut(
        user_id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=user.role,
        brands=_user_brands_out(db, db_user),
    )
