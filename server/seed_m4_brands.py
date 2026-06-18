#!/usr/bin/env python3
"""
M4 方案B · 业务真品牌主数据（保留 brand_id 1～5）
用法: cd server && python3 seed_m4_brands.py
"""

from pathlib import Path

import pymysql

from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
from seed_m3_auth import seed_users
from seed_m4_demo_metrics import apply_demo_metrics
from database import SessionLocal

MIGRATE_SQL = Path(__file__).resolve().parent.parent / "database" / "migrate_m4_real_brands.sql"
CONTENT_SQL = Path(__file__).resolve().parent.parent / "database" / "migrate_m4_real_brand_content.sql"


def _run_sql_file(path: Path, label: str):
    sql = path.read_text(encoding="utf-8")
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
    )
    try:
        with conn.cursor() as cur:
            for stmt in sql.split(";"):
                line = stmt.strip()
                if not line or line.startswith("--") or line.upper().startswith("USE "):
                    continue
                cur.execute(line)
        conn.commit()
        print(f"OK: {label} 已执行")
    finally:
        conn.close()


def apply_sql_migration():
    _run_sql_file(MIGRATE_SQL, "migrate_m4_real_brands")
    if CONTENT_SQL.exists():
        _run_sql_file(CONTENT_SQL, "migrate_m4_real_brand_content")


def main():
    apply_sql_migration()
    db = SessionLocal()
    try:
        seed_users(db)
        n = apply_demo_metrics(db)
        db.commit()
        if n:
            print(f"OK: 示范指标 {n} 条（类目/广告/P0）")
    finally:
        db.close()
    print("seed_m4_brands 完成 · 测试账号已按新 name_key 绑定")


if __name__ == "__main__":
    main()
