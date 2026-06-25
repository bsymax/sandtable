#!/usr/bin/env python3
"""
M4 · bi_csv 未覆盖字段写入示范指标（类目/广告/P0）
口径见 docs/数仓字段口径-v1.md · 与佳璇 jiaxuan-m4-0622/backend/seed.py 一致

用法: cd server && python3 seed_m4_demo_metrics.py
"""

from __future__ import annotations

import json

from database import SessionLocal
from models import Brand, BrandMetrics

# 底表暂无 · 写入 DB · 前端标注【示范数据】（类目已接 brand_category_monthly.csv）
DEMO_METRICS_BY_KEY = {
    "jomoo": dict(
        gross_margin=28.6,
        uv_conversion=4.9,
        ad_rate=6.1,
        p0_gap_count=2,
    ),
    "arrow": dict(
        gross_margin=26.2,
        uv_conversion=4.5,
        ad_rate=5.8,
        p0_gap_count=1,
    ),
    "hegii": dict(
        gross_margin=30.1,
        uv_conversion=5.2,
        ad_rate=7.0,
        p0_gap_count=1,
    ),
    "submarine": dict(
        gross_margin=32.4,
        uv_conversion=5.6,
        ad_rate=4.5,
        p0_gap_count=2,
    ),
    "micoe": dict(
        gross_margin=24.8,
        uv_conversion=4.2,
        ad_rate=5.5,
        p0_gap_count=1,
    ),
}


def apply_demo_metrics(db) -> int:
    """为 monthly 行补示范字段；不覆盖 bi_csv 已有 gmv 等真数字段。"""
    brands_by_key = {b.name_key: b for b in db.query(Brand).all()}
    count = 0
    for name_key, demo in DEMO_METRICS_BY_KEY.items():
        brand = brands_by_key.get(name_key)
        if not brand:
            continue
        payload = dict(demo)
        if payload.get("category_distribution") and not isinstance(payload["category_distribution"], str):
            payload["category_distribution"] = json.dumps(
                payload["category_distribution"], ensure_ascii=False
            )
        if payload.get("category_share") and not isinstance(payload["category_share"], str):
            payload["category_share"] = json.dumps(payload["category_share"], ensure_ascii=False)
        rows = (
            db.query(BrandMetrics)
            .filter(BrandMetrics.brand_id == brand.id, BrandMetrics.period_type == "monthly")
            .all()
        )
        for row in rows:
            for k, v in payload.items():
                setattr(row, k, v)
            count += 1
    return count


def main() -> None:
    db = SessionLocal()
    try:
        n = apply_demo_metrics(db)
        db.commit()
        print(f"seed_m4_demo_metrics 完成 · 已写入 {n} 条 monthly 示范字段")
    finally:
        db.close()


if __name__ == "__main__":
    main()
