#!/usr/bin/env python3
"""
M3-A 测试账号种子
用法: cd server && python3 seed_m3_auth.py

默认密码均为 sand123（仅本机/演示环境）
"""

from auth_utils import hash_password
from database import SessionLocal
from models import Brand, User, UserBrand

DEFAULT_PASSWORD = "sand123"

# username -> (display_name, role, brand name_keys)
ACCOUNTS = [
    ("admin", "系统管理员", "admin", []),
    ("zhou", "周采销", "bd", ["midea"]),
    ("wu", "吴采销", "bd", ["joyoung"]),
    ("chen", "陈采销", "bd", ["supor"]),
    ("li", "李采销", "bd", ["bear"]),
    ("wang", "王采销", "bd", ["morphy"]),
    ("demo", "演示账号", "manager", ["midea", "joyoung", "supor"]),
    ("readonly", "只读访客", "readonly", ["bear"]),
]


def _brand_map(db):
    rows = (
        db.query(Brand.id, Brand.name_key)
        .filter(Brand.status == "active")
        .all()
    )
    return {name_key: brand_id for brand_id, name_key in rows}


def seed_users(db):
    brand_ids = _brand_map(db)
    pwd_hash = hash_password(DEFAULT_PASSWORD)
    created = 0

    for username, display_name, role, keys in ACCOUNTS:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            user = User(
                username=username,
                password_hash=pwd_hash,
                display_name=display_name,
                role=role,
                is_active=True,
            )
            db.add(user)
            db.flush()
            created += 1
        else:
            user.display_name = display_name
            user.role = role
            user.password_hash = pwd_hash
            user.is_active = True

        db.query(UserBrand).filter(UserBrand.user_id == user.id).delete()
        if role != "admin":
            for key in keys:
                bid = brand_ids.get(key)
                if bid:
                    db.add(UserBrand(user_id=user.id, brand_id=bid))

    db.commit()
    print(f"seed_m3_auth 完成：新建 {created} 个账号，共 {len(ACCOUNTS)} 个测试用户，密码 {DEFAULT_PASSWORD}")


def main():
    db = SessionLocal()
    try:
        seed_users(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
