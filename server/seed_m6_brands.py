#!/usr/bin/env python3
"""
M6-A · 11 品牌槽位（KA 5 + 基础建材 6 真名）
用法: cd server && python3 seed_m6_brands.py
"""

import json
from pathlib import Path

from database import SessionLocal
from models import Brand

MASTER = Path(__file__).resolve().parent.parent / "data" / "brands_master.json"

# id → 原 M6 占位 key（便于 jc_* 行就地改名，保留 brand_id FK）
SLOT_OLD_KEYS = {
    6: "jc_a",
    7: "jc_b",
    8: "jc_c",
    9: "jc_d",
    10: "jc_e",
    11: "jc_f",
}


def _find_brand(db, row: dict):
    bid = row.get("id")
    key = row["name_key"]
    if bid:
        brand = db.query(Brand).filter(Brand.id == bid).first()
        if brand:
            return brand
    brand = db.query(Brand).filter(Brand.name_key == key).first()
    if brand:
        return brand
    old_key = SLOT_OLD_KEYS.get(bid or 0)
    if old_key:
        return db.query(Brand).filter(Brand.name_key == old_key).first()
    return None


def main():
    data = json.loads(MASTER.read_text(encoding="utf-8"))
    db = SessionLocal()
    created = updated = 0
    try:
        for row in data.get("brands") or []:
            key = row["name_key"]
            brand = _find_brand(db, row)
            if brand:
                brand.name = row["name"]
                brand.name_key = key
                brand.level = row.get("level", brand.level or "B")
                brand.responsible = row.get("responsible") or brand.responsible
                brand.status = "active"
                updated += 1
            else:
                kwargs = dict(
                    name=row["name"],
                    name_key=key,
                    level=row.get("level", "B"),
                    responsible=row.get("responsible"),
                    status="active",
                )
                if row.get("id"):
                    kwargs["id"] = row["id"]
                db.add(Brand(**kwargs))
                created += 1
        db.commit()
        total = db.query(Brand).filter(Brand.status == "active").count()
        print(f"seed_m6_brands 完成 · created={created} updated={updated} · active={total}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
