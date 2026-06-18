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

# 底表暂无 · 写入 DB · 前端标注【示范数据】
DEMO_METRICS_BY_KEY = {
    "jomoo": dict(
        category_distribution=[
            {"name": "智能马桶", "share": 32},
            {"name": "花洒", "share": 24},
            {"name": "浴室柜", "share": 18},
            {"name": "马桶", "share": 15},
            {"name": "龙头", "share": 11},
        ],
        category_share=[
            {"name": "智能马桶", "jd_share": 42, "avg": 30, "tm": 26, "tb": 14, "dy": 18},
            {"name": "花洒", "jd_share": 36, "avg": 28, "tm": 30, "tb": 16, "dy": 18},
            {"name": "浴室柜", "jd_share": 28, "avg": 22, "tm": 32, "tb": 20, "dy": 20},
        ],
        gross_margin=28.6,
        uv_conversion=4.9,
        ad_rate=6.1,
        p0_gap_count=2,
    ),
    "arrow": dict(
        category_distribution=[
            {"name": "智能马桶", "share": 28},
            {"name": "陶瓷马桶", "share": 26},
            {"name": "花洒", "share": 22},
            {"name": "浴室柜", "share": 14},
            {"name": "龙头", "share": 10},
        ],
        category_share=[
            {"name": "智能马桶", "jd_share": 34, "avg": 30, "tm": 32, "tb": 18, "dy": 16},
            {"name": "陶瓷马桶", "jd_share": 31, "avg": 26, "tm": 28, "tb": 22, "dy": 19},
        ],
        gross_margin=26.2,
        uv_conversion=4.5,
        ad_rate=5.8,
        p0_gap_count=1,
    ),
    "hegii": dict(
        category_distribution=[
            {"name": "智能马桶", "share": 35},
            {"name": "陶瓷洁具", "share": 25},
            {"name": "花洒", "share": 20},
            {"name": "浴室柜", "share": 12},
            {"name": "五金", "share": 8},
        ],
        category_share=[
            {"name": "智能马桶", "jd_share": 38, "avg": 32, "tm": 28, "tb": 16, "dy": 18},
            {"name": "陶瓷洁具", "jd_share": 30, "avg": 24, "tm": 34, "tb": 20, "dy": 16},
        ],
        gross_margin=30.1,
        uv_conversion=5.2,
        ad_rate=7.0,
        p0_gap_count=1,
    ),
    "submarine": dict(
        category_distribution=[
            {"name": "地漏", "share": 38},
            {"name": "角阀", "share": 22},
            {"name": "花洒", "share": 18},
            {"name": "龙头", "share": 12},
            {"name": "卫浴配件", "share": 10},
        ],
        category_share=[
            {"name": "地漏", "jd_share": 48, "avg": 35, "tm": 22, "tb": 18, "dy": 12},
            {"name": "角阀", "jd_share": 40, "avg": 28, "tm": 26, "tb": 20, "dy": 14},
        ],
        gross_margin=32.4,
        uv_conversion=5.6,
        ad_rate=4.5,
        p0_gap_count=2,
    ),
    "micoe": dict(
        category_distribution=[
            {"name": "太阳能热水器", "share": 36},
            {"name": "电热水器", "share": 24},
            {"name": "花洒", "share": 18},
            {"name": "浴室柜", "share": 12},
            {"name": "龙头", "share": 10},
        ],
        category_share=[
            {"name": "太阳能热水器", "jd_share": 26, "avg": 22, "tm": 30, "tb": 24, "dy": 20},
            {"name": "电热水器", "jd_share": 28, "avg": 24, "tm": 28, "tb": 22, "dy": 22},
        ],
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
