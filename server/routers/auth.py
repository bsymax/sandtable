"""
M3/M5 登录与账号管理
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from auth_utils import (
    generate_temp_password,
    hash_password,
    hash_password_sha256,
    new_session_token,
    session_expires_at,
    validate_new_password,
    verify_password,
)
from brand_keys import resolve_brand_keys
from database import get_db
from deps_auth import AuthUser, get_admin_user, get_current_user, get_current_user_optional
from models import Brand, User, UserBrand, UserSession
from schemas import (
    AdminUserBrandsIn,
    AdminUserCreateIn,
    AdminUserOut,
    AdminUserUpdateIn,
    ChangePasswordIn,
    ChangePasswordOut,
    LoginIn,
    LoginOut,
    MeOut,
    ResetPasswordOut,
    UserBrandOut,
)

router = APIRouter()

VALID_ROLES = {"admin", "bd", "manager", "readonly"}


def _brand_map(db: Session) -> dict:
    rows = db.query(Brand.id, Brand.name_key).filter(Brand.status == "active").all()
    return {name_key: brand_id for brand_id, name_key in rows}


def _user_brands_out(db: Session, user: User) -> list:
    if user.role == "admin":
        brands = db.query(Brand).filter(Brand.status == "active").order_by(Brand.id).all()
    else:
        ids = [ub.brand_id for ub in (user.brands or [])]
        brands = (
            db.query(Brand).filter(Brand.id.in_(ids), Brand.status == "active").order_by(Brand.id).all()
            if ids
            else []
        )
    return [UserBrandOut(id=b.id, name=b.name, name_key=b.name_key, level=b.level) for b in brands]


def _admin_user_out(db: Session, user: User) -> AdminUserOut:
    return AdminUserOut(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        dept=user.dept,
        role=user.role,
        is_active=bool(user.is_active),
        must_change_password=bool(user.must_change_password),
        last_login_at=user.last_login_at,
        brands=_user_brands_out(db, user),
    )


def _apply_brand_keys(db: Session, user: User, brand_keys: List[str]) -> None:
    if user.role == "admin":
        db.query(UserBrand).filter(UserBrand.user_id == user.id).delete()
        return
    brand_ids = _brand_map(db)
    active = set(brand_ids.keys())
    keys, _unknown = resolve_brand_keys(brand_keys, active)
    db.query(UserBrand).filter(UserBrand.user_id == user.id).delete()
    for key in keys:
        bid = brand_ids.get(key)
        if bid:
            db.add(UserBrand(user_id=user.id, brand_id=bid))


def _login_response(db: Session, user: User, token: str) -> LoginOut:
    return LoginOut(
        token=token,
        user_id=user.id,
        username=user.username,
        display_name=user.display_name,
        dept=user.dept,
        role=user.role,
        must_change_password=bool(user.must_change_password),
        brands=_user_brands_out(db, user),
    )


@router.post("/api/auth/login", response_model=LoginOut, tags=["登录"])
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username, User.is_active == True).first()
    algo = getattr(user, "password_algo", "sha256") if user else "sha256"
    if not user or not verify_password(payload.password, user.password_hash, algo):
        raise HTTPException(401, "用户名或密码错误")
    token = new_session_token()
    user.last_login_at = datetime.utcnow()
    db.add(UserSession(user_id=user.id, token=token, expires_at=session_expires_at()))
    db.commit()
    db.refresh(user)
    return _login_response(db, user, token)


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
        dept=db_user.dept,
        role=user.role,
        must_change_password=bool(db_user.must_change_password),
        brands=_user_brands_out(db, db_user),
    )


@router.post("/api/auth/change-password", response_model=ChangePasswordOut, tags=["登录"])
def change_password(
    payload: ChangePasswordIn,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    db_user = db.query(User).filter(User.id == user.id).first()
    if not db_user:
        raise HTTPException(401, "用户不存在")
    algo = getattr(db_user, "password_algo", "sha256") or "sha256"
    if not verify_password(payload.old_password, db_user.password_hash, algo):
        raise HTTPException(400, "原密码错误")
    err = validate_new_password(db_user.username, payload.new_password)
    if err:
        raise HTTPException(400, err)
    new_hash, new_algo = hash_password(payload.new_password)
    db_user.password_hash = new_hash
    db_user.password_algo = new_algo
    db_user.must_change_password = False
    db.commit()
    return ChangePasswordOut(must_change_password=False)


@router.get("/api/auth/admin/users", response_model=List[AdminUserOut], tags=["账号管理"])
def admin_list_users(
    db: Session = Depends(get_db),
    admin: AuthUser = Depends(get_admin_user),
):
    users = db.query(User).order_by(User.id).all()
    return [_admin_user_out(db, u) for u in users]


@router.post("/api/auth/admin/users", response_model=AdminUserOut, tags=["账号管理"])
def admin_create_user(
    payload: AdminUserCreateIn,
    db: Session = Depends(get_db),
    admin: AuthUser = Depends(get_admin_user),
):
    username = payload.username.strip().lower()
    if not username:
        raise HTTPException(400, "username 不能为空")
    if payload.role not in VALID_ROLES:
        raise HTTPException(400, f"role 须为 {sorted(VALID_ROLES)}")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(409, "用户名已存在")
    raw_pwd = payload.password or generate_temp_password()
    err = validate_new_password(username, raw_pwd)
    if err:
        raise HTTPException(400, err)
    pwd_hash, pwd_algo = hash_password(raw_pwd)
    user = User(
        username=username,
        password_hash=pwd_hash,
        password_algo=pwd_algo,
        display_name=payload.display_name.strip(),
        dept=(payload.dept or "").strip() or None,
        role=payload.role,
        is_active=True,
        must_change_password=True,
    )
    db.add(user)
    db.flush()
    _apply_brand_keys(db, user, payload.brand_keys)
    db.commit()
    db.refresh(user)
    return _admin_user_out(db, user)


@router.patch("/api/auth/admin/users/{user_id}", response_model=AdminUserOut, tags=["账号管理"])
def admin_update_user(
    user_id: int,
    payload: AdminUserUpdateIn,
    db: Session = Depends(get_db),
    admin: AuthUser = Depends(get_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    if payload.display_name is not None:
        user.display_name = payload.display_name.strip()
    if payload.dept is not None:
        user.dept = payload.dept.strip() or None
    if payload.role is not None:
        if payload.role not in VALID_ROLES:
            raise HTTPException(400, f"role 须为 {sorted(VALID_ROLES)}")
        user.role = payload.role
        if payload.role == "admin":
            db.query(UserBrand).filter(UserBrand.user_id == user.id).delete()
    if payload.is_active is not None:
        user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return _admin_user_out(db, user)


@router.post("/api/auth/admin/users/{user_id}/reset-password", response_model=ResetPasswordOut, tags=["账号管理"])
def admin_reset_password(
    user_id: int,
    db: Session = Depends(get_db),
    admin: AuthUser = Depends(get_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    temp = generate_temp_password()
    pwd_hash, pwd_algo = hash_password(temp)
    user.password_hash = pwd_hash
    user.password_algo = pwd_algo
    user.must_change_password = True
    db.commit()
    return ResetPasswordOut(temp_password=temp)


@router.post("/api/auth/admin/users/{user_id}/brands", response_model=AdminUserOut, tags=["账号管理"])
def admin_set_user_brands(
    user_id: int,
    payload: AdminUserBrandsIn,
    db: Session = Depends(get_db),
    admin: AuthUser = Depends(get_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    _apply_brand_keys(db, user, payload.brand_keys)
    db.commit()
    db.refresh(user)
    return _admin_user_out(db, user)
