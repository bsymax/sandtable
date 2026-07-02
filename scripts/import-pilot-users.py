#!/usr/bin/env python3
"""
M5-C 试点名单 CSV 导入（Max 执行 · 开开交 CSV）
用法:
  cd server && python3 ../scripts/import-pilot-users.py ../docs/templates/pilot-users-v1.example.csv --dry-run
  cd server && python3 ../scripts/import-pilot-users.py ../path/to/pilot-users-v1.csv

CSV 列: username,display_name,role,brand_keys,dept
brand_keys 支持 legacy 别名（midea→jomoo 等，见 data/brands_master.json）
禁止 CSV 含 password 列。
"""

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "server"))

from auth_utils import generate_temp_password, hash_password, validate_new_password  # noqa: E402
from brand_keys import load_legacy_name_key_map, resolve_brand_keys  # noqa: E402
from database import SessionLocal  # noqa: E402
from models import Brand, User, UserBrand  # noqa: E402

VALID_ROLES = {"admin", "bd", "manager", "readonly"}
REQUIRED = {"username", "display_name", "role"}


def _brand_map(db):
    rows = db.query(Brand.id, Brand.name_key).filter(Brand.status == "active").all()
    return {name_key: brand_id for brand_id, name_key in rows}


def _active_keys(brand_ids: dict) -> set:
    return set(brand_ids.keys())


def _parse_brand_keys(raw: str) -> list:
    if not raw or not str(raw).strip():
        return []
    return [k.strip() for k in str(raw).split(",") if k.strip()]


def load_rows(path: Path) -> list:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise SystemExit("CSV 无表头")
        fields = {c.strip() for c in reader.fieldnames}
        if "password" in fields:
            raise SystemExit("禁止 CSV 含 password 列")
        missing = REQUIRED - fields
        if missing:
            raise SystemExit(f"CSV 缺列: {sorted(missing)}")
        return list(reader)


def import_users(db, rows, dry_run: bool, strict: bool, preset_password: str | None = None) -> dict:
    brand_ids = _brand_map(db)
    active = _active_keys(brand_ids)
    legacy = load_legacy_name_key_map()
    stats = {
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "bindings": 0,
        "legacy_mapped": 0,
        "passwords": [],
    }

    print(f"    库内品牌: {', '.join(sorted(active))}")
    if legacy:
        print(f"    legacy 映射: {len(legacy)} 条（如 midea→jomoo）")

    for i, row in enumerate(rows, start=2):
        username = (row.get("username") or "").strip().lower()
        display_name = (row.get("display_name") or "").strip()
        role = (row.get("role") or "").strip()
        dept = (row.get("dept") or "").strip() or None
        raw_keys = _parse_brand_keys(row.get("brand_keys") or "")
        keys, unknown = resolve_brand_keys(raw_keys, active)

        if not username or not display_name:
            print(f"  行{i} 跳过：username/display_name 为空")
            stats["skipped"] += 1
            continue
        if role not in VALID_ROLES:
            print(f"  行{i} 跳过：非法 role {role}")
            stats["skipped"] += 1
            continue
        if unknown:
            msg = f"  行{i} 未知 brand_key: {unknown}（raw={raw_keys}）"
            if strict:
                raise SystemExit(msg)
            print(msg + " · 该行品牌绑定将跳过未知项")
        if raw_keys and keys and raw_keys != keys:
            stats["legacy_mapped"] += 1

        user = db.query(User).filter(User.username == username).first()
        if preset_password:
            temp_pwd = preset_password
        else:
            temp_pwd = generate_temp_password()
        err = validate_new_password(username, temp_pwd)
        if err:
            raise SystemExit(f"行{i} 临时密码生成失败: {err}")
        pwd_hash, pwd_algo = hash_password(temp_pwd)

        if user:
            user.display_name = display_name
            user.role = role
            user.dept = dept
            user.is_active = True
            user.password_hash = pwd_hash
            user.password_algo = pwd_algo
            user.must_change_password = True
            db.query(UserBrand).filter(UserBrand.user_id == user.id).delete()
            stats["updated"] += 1
        else:
            user = User(
                username=username,
                password_hash=pwd_hash,
                password_algo=pwd_algo,
                display_name=display_name,
                dept=dept,
                role=role,
                is_active=True,
                must_change_password=True,
            )
            db.add(user)
            db.flush()
            stats["created"] += 1

        if role != "admin":
            for key in keys:
                bid = brand_ids.get(key)
                if bid:
                    db.add(UserBrand(user_id=user.id, brand_id=bid))
                    stats["bindings"] += 1

        stats["passwords"].append((username, temp_pwd))
        raw_disp = ",".join(raw_keys) if raw_keys else "-"
        canon_disp = ",".join(keys) if keys else "-"
        map_note = f" (→ {canon_disp})" if raw_keys and canon_disp != raw_disp else ""
        print(f"  {'[dry-run] ' if dry_run else ''}行{i} {username} ({role}) brands={raw_disp}{map_note}")

    if dry_run:
        db.rollback()
    else:
        db.commit()
    return stats


def main():
    parser = argparse.ArgumentParser(description="M5 试点名单导入")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="不写库，仅校验与预览")
    parser.add_argument("--strict", action="store_true", help="未知 brand_key 立即失败")
    parser.add_argument(
        "--preset-password",
        metavar="PWD",
        help="M6 统一初始密码（全员相同；须满足密码强度规则）",
    )
    args = parser.parse_args()

    if not args.csv_path.is_file():
        raise SystemExit(f"文件不存在: {args.csv_path}")

    rows = load_rows(args.csv_path)
    if len(rows) < 1:
        raise SystemExit("CSV 无数据行")

    if args.preset_password:
        err = validate_new_password("_preset_check", args.preset_password)
        if err:
            raise SystemExit(f"--preset-password 不符合规则: {err}")

    db = SessionLocal()
    try:
        print(f"==> 导入 {args.csv_path.name} · {len(rows)} 行 · dry_run={args.dry_run}")
        if args.preset_password:
            print("    使用统一初始密码（M6 模式）")
        stats = import_users(db, rows, args.dry_run, args.strict, args.preset_password)
        print(
            f"==> 完成 created={stats['created']} updated={stats['updated']} "
            f"skipped={stats['skipped']} bindings={stats['bindings']} "
            f"legacy_rows={stats['legacy_mapped']}"
        )
        if not args.dry_run:
            out = args.csv_path.with_suffix(".passwords.txt")
            with out.open("w", encoding="utf-8") as f:
                f.write("# 临时密码 · 仅 Max 保管 · 勿进 git\n")
                for u, p in stats["passwords"]:
                    f.write(f"{u}\t{p}\n")
            print(f"    临时密码已写 {out.name}（勿提交 git）")
    finally:
        db.close()


if __name__ == "__main__":
    main()
