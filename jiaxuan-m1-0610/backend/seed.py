"""
初始化 brand_profiles / brand_metrics 种子数据
"""

from datetime import datetime

from database import SessionLocal, engine
from models import Base, Brand, BrandProfile, BrandMetrics


PROFILES = [
    dict(brand_id=1, founded_year="1968年", hq="广东佛山顺德",
         positioning="全球化科技集团，智能家居与全品类家电龙头；多品牌矩阵（美的/COLMO/东芝等），全渠道+DTC转型中。",
         org_structure='{"root":"美的集团","lead":"电商事业部","nodes":["王建国 · 总经理","李敏 · 渠道","张磊 · 产品"]}',
         taboos="王总不喜欢饭局谈正事，建议工作日早上10点前约短会。\n合同谈判偏好：先邮件沟通条款，再面谈拍板。",
         taboo_updated_by="周采销", taboo_updated_at=datetime(2026, 5, 20, 10, 0, 0)),
    dict(brand_id=2, founded_year="1994年", hq="山东济南",
         positioning="原创创新与健康生活方式的品质小家电品牌；豆浆机起家，破壁机/电饭煲/空气炸锅等厨电全品类布局。",
         org_structure='{"root":"九阳股份","lead":"电商中心","nodes":["陈志远 · VP","赵雪 · JD渠道","供应链 · 待补"]}',
         taboos="VP层级会议需提前3天邮件预约，附带JD数据简报。",
         taboo_updated_by="吴采销", taboo_updated_at=datetime(2026, 3, 12, 9, 0, 0)),
    dict(brand_id=3, founded_year="1994年", hq="浙江杭州（制造基地玉环）",
         positioning="中国炊具与小家电行业领跑者，SEB集团旗下；明火炊具+厨房小家电+生活家居多品类，注重ROI与品牌矩阵。",
         org_structure='{"root":"苏泊尔集团","lead":"电商部","nodes":["总监 · 待核实","京东组 · 待补"]}',
         taboos="品牌方当前更关注ROI，大规模要量易被拒，建议带数据方案。",
         taboo_updated_by="陈采销", taboo_updated_at=datetime(2026, 2, 18, 14, 0, 0)),
    dict(brand_id=4, founded_year="2006年", hq="广东佛山顺德",
         positioning="「年轻人喜欢的小家电」——创意小电品牌，养生壶/电饭煲mini等细分品类领先，线上渠道优势明显。",
         org_structure='{"root":"小熊电器","lead":"电商部","nodes":["林晓 · 总监","周帆 · 产品","市场 · 联名"]}',
         taboos="品牌方对联名款创意敏感，需带视觉草案再谈，避免空口承诺。",
         taboo_updated_by="李采销", taboo_updated_at=datetime(2026, 5, 18, 11, 0, 0)),
    dict(brand_id=5, founded_year="1936年", hq="英国品牌 / 中国运营：广东佛山",
         positioning="英伦高端创意小电，1936年英国创立；2013年由新宝股份引入中国，抖音/小红书内容电商强势，JD渠道待深化。",
         org_structure='{"root":"新宝股份","lead":"摩飞品牌事业部","nodes":["总监 · 待补","私域 · 待补","产品 · 待补"]}',
         taboos="（待补全）决策人偏好与拜访禁忌尚未录入。",
         taboo_updated_by=None, taboo_updated_at=None),
]

# 12 周 GMV 趋势（万元），末周与当前种子一致
WEEKLY_GMV_TRENDS = {
    1: [607, 624, 647, 630, 635, 618, 601, 578, 555, 532, 508, 487],
    2: [350, 356, 362, 365, 368, 372, 378, 385, 420, 460, 490, 512],
    3: [569, 574, 580, 586, 592, 598, 604, 610, 616, 620, 622, 623],
    4: [218, 225, 232, 238, 245, 252, 260, 268, 276, 285, 292, 298],
    5: [137, 141, 145, 148, 152, 156, 162, 168, 174, 180, 184, 187],
}

METRIC_TEMPLATES = {
    1: dict(gmv_yoy=-8.1, orders=48200, orders_wow=-12, jd_share=31.2, jd_share_wow=-2.1,
            tmall_share=24.8, douyin_share=28.5, pdd_share=8.2,
            channel_growth_jd=-16.3, channel_growth_tmall=-5.2, channel_growth_douyin=22,
            category_distribution='[{"name":"空气炸锅","share":22},{"name":"电饭煲","share":17},{"name":"破壁机","share":12}]',
            category_share='[{"name":"空气炸锅","jd_share":28,"avg":22},{"name":"电饭煲","jd_share":31,"avg":24}]',
            sku_count=428, p0_gap_count=3, gross_margin=22.4, uv_conversion=4.2, ad_rate=5.0),
    2: dict(gmv_yoy=6.2, orders=22800, orders_wow=4.5, jd_share=18.5, jd_share_wow=0.8,
            tmall_share=28, douyin_share=32, pdd_share=12,
            channel_growth_jd=3.2, channel_growth_tmall=2.1, channel_growth_douyin=45,
            category_distribution='[{"name":"破壁机","share":24},{"name":"豆浆机","share":18}]',
            category_share='[{"name":"破壁机","jd_share":22,"avg":20}]',
            sku_count=186, p0_gap_count=2, gross_margin=26.8, uv_conversion=5.1, ad_rate=3.8),
    3: dict(gmv_yoy=4.2, orders=16500, orders_wow=3.8, jd_share=14.2, jd_share_wow=-1.5,
            tmall_share=32, douyin_share=22, pdd_share=14,
            channel_growth_jd=5, channel_growth_tmall=3, channel_growth_douyin=8,
            category_distribution='[{"name":"电饭煲","share":28},{"name":"破壁机","share":20}]',
            category_share='[{"name":"电饭煲","jd_share":16,"avg":22}]',
            sku_count=152, p0_gap_count=1, gross_margin=24.1, uv_conversion=4.6, ad_rate=7.5),
    4: dict(gmv_yoy=18, orders=11200, orders_wow=18, jd_share=38, jd_share_wow=3.5,
            tmall_share=22, douyin_share=28, pdd_share=8,
            channel_growth_jd=15, channel_growth_tmall=8, channel_growth_douyin=35,
            category_distribution='[{"name":"养生壶","share":33},{"name":"电饭煲mini","share":24}]',
            category_share='[{"name":"养生壶","jd_share":42,"avg":18}]',
            sku_count=96, p0_gap_count=0, gross_margin=28.5, uv_conversion=5.8, ad_rate=3.2),
    5: dict(gmv_yoy=10, orders=6800, orders_wow=6, jd_share=18.5, jd_share_wow=0.5,
            tmall_share=20, douyin_share=45, pdd_share=10,
            channel_growth_jd=8, channel_growth_tmall=5, channel_growth_douyin=38,
            category_distribution='[{"name":"多功能锅","share":35},{"name":"榨汁机","share":22}]',
            category_share='[{"name":"多功能锅","jd_share":12,"avg":22}]',
            sku_count=64, p0_gap_count=4, gross_margin=32.1, uv_conversion=3.8, ad_rate=2.1),
}


def _calc_wow(current, previous):
    if not previous:
        return 0
    return round((current - previous) / previous * 100, 2)


def seed_weekly_history(db):
    """为每个品牌补全 12 周 brand_metrics 记录"""
    for brand_id, trend in WEEKLY_GMV_TRENDS.items():
        count = (
            db.query(BrandMetrics)
            .filter(BrandMetrics.brand_id == brand_id, BrandMetrics.period_type == "weekly")
            .count()
        )
        if count >= 12:
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
        print(f"brand_id={brand_id} 已导入 12 周 metrics")


def run_seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(BrandProfile).count() == 0:
            brand_count = db.query(Brand).count()
            if brand_count < 5:
                print(f"警告：brands 表仅 {brand_count} 条，请先导入培翛 schema.sql")
            for row in PROFILES:
                db.add(BrandProfile(**row))
            db.commit()
            print("种子数据导入完成：5 条 profile")
        else:
            print("brand_profiles 已有数据，跳过 profile 导入")

        seed_weekly_history(db)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
