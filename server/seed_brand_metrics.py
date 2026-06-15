#!/usr/bin/env python3
"""
brand_metrics 演示数据补全（佳璇 0615 补丁 · Max 合并版）
- 每品牌 12 周 GMV 历史
- 类目 JSON（JD/TM/TB/DY 四渠道）

用法（项目根或 server 目录）:
  cd server && python3 seed_brand_metrics.py
"""

from database import SessionLocal
from models import BrandMetrics

WEEKLY_GMV_TRENDS = {
    1: [607, 624, 647, 630, 635, 618, 601, 578, 555, 532, 508, 487],
    2: [350, 356, 362, 365, 368, 372, 378, 385, 420, 460, 490, 512],
    3: [569, 574, 580, 586, 592, 598, 604, 610, 616, 620, 622, 623],
    4: [218, 225, 232, 238, 245, 252, 260, 268, 276, 285, 292, 298],
    5: [137, 141, 145, 148, 152, 156, 162, 168, 174, 180, 184, 187],
}

METRIC_TEMPLATES = {
    1: dict(
        gmv_yoy=-8.1, sales_volume=48200, sales_volume_wow=-12, jd_share=31.2, jd_share_wow=-2.1,
        tmall_share=24.8, douyin_share=28.5, pdd_share=8.2,
        channel_growth_jd=-16.3, channel_growth_tmall=-5.2, channel_growth_douyin=22,
        category_distribution='[{"name":"空气炸锅","share":22},{"name":"电饭煲","share":17},{"name":"破壁机","share":12}]',
        category_share='[{"name":"空气炸锅","jd":38,"tm":28,"tb":12,"dy":22,"jd_platform_share":18},{"name":"电饭煲","jd":42,"tm":25,"tb":8,"dy":25,"jd_platform_share":24},{"name":"破壁机","jd":35,"tm":22,"tb":15,"dy":28,"jd_platform_share":15}]',
        sku_count=428, p0_gap_count=3, gross_margin=22.4, uv_conversion=4.2, ad_rate=5.0,
    ),
    2: dict(
        gmv_yoy=6.2, sales_volume=22800, sales_volume_wow=4.5, jd_share=18.5, jd_share_wow=0.8,
        tmall_share=28, douyin_share=32, pdd_share=12,
        channel_growth_jd=3.2, channel_growth_tmall=2.1, channel_growth_douyin=45,
        category_distribution='[{"name":"破壁机","share":24},{"name":"豆浆机","share":18}]',
        category_share='[{"name":"破壁机","jd":32,"tm":26,"tb":10,"dy":32,"jd_platform_share":20},{"name":"豆浆机","jd":28,"tm":30,"tb":14,"dy":28,"jd_platform_share":16}]',
        sku_count=186, p0_gap_count=2, gross_margin=26.8, uv_conversion=5.1, ad_rate=3.8,
    ),
    3: dict(
        gmv_yoy=4.2, sales_volume=16500, sales_volume_wow=3.8, jd_share=14.2, jd_share_wow=-1.5,
        tmall_share=32, douyin_share=22, pdd_share=14,
        channel_growth_jd=5, channel_growth_tmall=3, channel_growth_douyin=8,
        category_distribution='[{"name":"电饭煲","share":28},{"name":"破壁机","share":20}]',
        category_share='[{"name":"电饭煲","jd":36,"tm":28,"tb":12,"dy":24,"jd_platform_share":22},{"name":"破壁机","jd":30,"tm":24,"tb":18,"dy":28,"jd_platform_share":18}]',
        sku_count=152, p0_gap_count=1, gross_margin=24.1, uv_conversion=4.6, ad_rate=7.5,
    ),
    4: dict(
        gmv_yoy=18, sales_volume=11200, sales_volume_wow=18, jd_share=38, jd_share_wow=3.5,
        tmall_share=22, douyin_share=28, pdd_share=8,
        channel_growth_jd=15, channel_growth_tmall=8, channel_growth_douyin=35,
        category_distribution='[{"name":"养生壶","share":33},{"name":"电饭煲mini","share":24}]',
        category_share='[{"name":"养生壶","jd":45,"tm":18,"tb":10,"dy":27,"jd_platform_share":18},{"name":"电饭煲mini","jd":40,"tm":22,"tb":12,"dy":26,"jd_platform_share":14}]',
        sku_count=96, p0_gap_count=0, gross_margin=28.5, uv_conversion=5.8, ad_rate=3.2,
    ),
    5: dict(
        gmv_yoy=10, sales_volume=6800, sales_volume_wow=6, jd_share=18.5, jd_share_wow=0.5,
        tmall_share=20, douyin_share=45, pdd_share=10,
        channel_growth_jd=8, channel_growth_tmall=5, channel_growth_douyin=38,
        category_distribution='[{"name":"多功能锅","share":35},{"name":"榨汁机","share":22}]',
        category_share='[{"name":"多功能锅","jd":22,"tm":20,"tb":18,"dy":40,"jd_platform_share":22},{"name":"榨汁机","jd":26,"tm":24,"tb":16,"dy":34,"jd_platform_share":12}]',
        sku_count=64, p0_gap_count=4, gross_margin=32.1, uv_conversion=3.8, ad_rate=2.1,
    ),
}


def _calc_wow(current, previous):
    if not previous:
        return 0
    return round((current - previous) / previous * 100, 2)


def seed_weekly_history(db):
    for brand_id, trend in WEEKLY_GMV_TRENDS.items():
        rows = (
            db.query(BrandMetrics)
            .filter(BrandMetrics.brand_id == brand_id, BrandMetrics.period_type == "weekly")
            .order_by(BrandMetrics.period_value.asc())
            .all()
        )
        gmvs = [float(r.gmv) for r in rows if r.gmv is not None]
        if len(rows) >= 12 and len(gmvs) >= 12:
            continue

        db.query(BrandMetrics).filter(
            BrandMetrics.brand_id == brand_id,
            BrandMetrics.period_type == "weekly",
        ).delete()

        template = METRIC_TEMPLATES[brand_id]
        prev_gmv = None
        for i, week_num in enumerate(range(12, 24)):
            gmv = trend[i]
            row = dict(
                brand_id=brand_id,
                period_type="weekly",
                period_value=f"2026W{week_num:02d}",
                gmv=gmv,
                gmv_wow=_calc_wow(gmv, prev_gmv),
                **template,
            )
            db.add(BrandMetrics(**row))
            prev_gmv = gmv
        print(f"brand_id={brand_id} 已刷新 12 周 metrics")


def refresh_category_metrics(db):
    for brand_id, template in METRIC_TEMPLATES.items():
        latest = (
            db.query(BrandMetrics)
            .filter(BrandMetrics.brand_id == brand_id, BrandMetrics.period_type == "weekly")
            .order_by(BrandMetrics.period_value.desc())
            .first()
        )
        if not latest:
            continue
        latest.category_distribution = template["category_distribution"]
        latest.category_share = template["category_share"]
        print(f"brand_id={brand_id} 已刷新类目渠道 JSON")


def main():
    db = SessionLocal()
    try:
        seed_weekly_history(db)
        refresh_category_metrics(db)
        db.commit()
        print("seed_brand_metrics 完成")
    finally:
        db.close()


if __name__ == "__main__":
    main()
