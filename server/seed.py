"""
初始化 brand_profiles / brand_metrics 种子数据
建材业务部-国内KA卫浴组 · 数据源见 data/dw/品牌档案数据源.xlsx
"""

import csv
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import inspect, text

from config import IS_SQLITE
from database import SessionLocal, engine
from models import Base, Brand, BrandProfile, BrandMetrics

DW_DIR = Path(__file__).resolve().parent.parent / "data" / "dw"
METRICS_CSV = DW_DIR / "brand_metrics_monthly.csv"
CATEGORY_CSV = DW_DIR / "brand_category_monthly.csv"
BRANDS_CSV = DW_DIR / "brands_master.csv"

BRANDS = [
    dict(id=1, name="九牧", name_key="jomoo", level="S", responsible="周采销", archive_score=85, relation_temp=78, baseline_freq="季度/次"),
    dict(id=2, name="箭牌", name_key="arrow", level="A", responsible="吴采销", archive_score=82, relation_temp=75, baseline_freq="季度/次"),
    dict(id=3, name="恒洁", name_key="hegii", level="A", responsible="陈采销", archive_score=80, relation_temp=72, baseline_freq="季度/次"),
    dict(id=4, name="潜水艇", name_key="submarine", level="B", responsible="李采销", archive_score=76, relation_temp=70, baseline_freq="季度/次"),
    dict(id=5, name="四季沐歌", name_key="micoe", level="B", responsible="王采销", archive_score=74, relation_temp=68, baseline_freq="季度/次"),
    dict(id=6, name="立邦", name_key="nippon", level="B", responsible="待定", archive_score=60, relation_temp=65, baseline_freq="季度/次"),
    dict(id=7, name="三棵树", name_key="skshu", level="B", responsible="待定", archive_score=60, relation_temp=65, baseline_freq="季度/次"),
    dict(id=8, name="多乐士", name_key="dulux", level="B", responsible="待定", archive_score=60, relation_temp=65, baseline_freq="季度/次"),
    dict(id=9, name="瓦克", name_key="wacker", level="B", responsible="待定", archive_score=60, relation_temp=65, baseline_freq="季度/次"),
    dict(id=10, name="雨虹防水", name_key="yuhong", level="B", responsible="待定", archive_score=60, relation_temp=65, baseline_freq="季度/次"),
    dict(id=11, name="嘉宝莉", name_key="carpoly", level="B", responsible="待定", archive_score=60, relation_temp=65, baseline_freq="季度/次"),
]

M2_PROFILE_DEFAULTS = {
    1: dict(
        competitive_landscape="（待补全竞争格局分析）",
        growth_opportunities="（待补全增长机会）",
    ),
    2: dict(
        competitive_landscape="（待补全竞争格局分析）",
        growth_opportunities="（待补全增长机会）",
    ),
    3: dict(
        competitive_landscape="（待补全竞争格局分析）",
        growth_opportunities="（待补全增长机会）",
    ),
    4: dict(
        competitive_landscape="（待补全竞争格局分析）",
        growth_opportunities="（待补全增长机会）",
    ),
    5: dict(
        competitive_landscape="（待补全竞争格局分析）",
        growth_opportunities="（待补全增长机会）",
    ),
}

# 旧 M2 seed 固定句 · 一次性重置为占位后走前端 buildStrategyFallback 规则
LEGACY_M2_STRATEGY_COMP = {
    "国内卫浴龙头，JD 市占领先；与箭牌、恒洁在智能马桶/花洒品类直接竞争。",
    "陶瓷卫浴核心品牌，TM/TB 份额较高；与九牧在 JD 智能马桶价格带重叠。",
    "中高端卫浴定位，全渠道布局；DY 增速波动需关注内容电商投入。",
    "五金地漏细分强势；卫浴主品类占比提升中。",
    "太阳能+卫浴延伸品牌，季节性强；DY/TB 占比较高。",
}
LEGACY_M2_STRATEGY_OPP = {
    "智能马桶品类可争取 JD 品类日；动销商品数（SPU）结构优化带动成交回升。",
    "JD 市占提升空间大，可谈联合搜索与新品首发。",
    "套餐化 SPU 引入 JD，提升客单与动销商品数宽度。",
    "地漏品类优势可带动卫浴配件组合装上架。",
    "旺季前锁定 JD 热水器/卫浴联合促销资源。",
}

JC_PROFILE_DEFAULTS = dict(
    competitive_landscape="（待补全竞争格局分析）",
    growth_opportunities="（待补全增长机会）",
)

M6_JC_PROFILES = [
    (6, "nippon", "立邦", "1881年", "上海", "NIPPON 立邦，涂料与建材；全渠道布局中。"),
    (7, "skshu", "三棵树", "2002年", "福建莆田", "三棵树 SKSHU，涂料建材；电商渠道拓展中。"),
    (8, "dulux", "多乐士", "—", "上海", "DULUX 多乐士，阿克苏诺贝尔旗下涂料品牌。"),
    (9, "wacker", "瓦克", "1914年", "德国/中国", "WACKER 瓦克，胶粘剂与化学建材。"),
    (10, "yuhong", "雨虹防水", "1995年", "北京", "东方雨虹系防水建材；京东品类渗透提升中。"),
    (11, "carpoly", "嘉宝莉", "1999年", "广东江门", "CARPOLY 嘉宝莉，涂料品牌。"),
]

PROFILES = [
    dict(brand_id=1, founded_year="1990年", hq="福建南安",
         positioning="综合性卫浴品牌，智能马桶与五金花洒为核心品类；国内 KA 渠道深度布局。",
         org_structure='{"root":"九牧集团","lead":"电商事业部","nodes":["电商总监 · 待补","JD渠道 · 待补"]}',
         taboos="（待补全）重大政策需书面确认后再对外承诺。",
         taboo_updated_by="周采销", taboo_updated_at=datetime(2026, 5, 15, 10, 0, 0),
         **M2_PROFILE_DEFAULTS[1]),
    dict(brand_id=2, founded_year="1994年", hq="广东佛山",
         positioning="ARROW 箭牌卫浴，陶瓷洁具与智能卫浴；全渠道经营，天猫传统优势。",
         org_structure='{"root":"箭牌家居","lead":"电商中心","nodes":["总监 · 待补","京东组 · 待补"]}',
         taboos="（待补全）",
         taboo_updated_by="吴采销", taboo_updated_at=datetime(2026, 4, 20, 9, 0, 0),
         **M2_PROFILE_DEFAULTS[2]),
    dict(brand_id=3, founded_year="1998年", hq="广东佛山",
         positioning="HEGII 恒洁卫浴，中高端定位；智能马桶与陶瓷洁具并重。",
         org_structure='{"root":"恒洁卫浴","lead":"电商部","nodes":["总监 · 待补"]}',
         taboos="（待补全）",
         taboo_updated_by="陈采销", taboo_updated_at=datetime(2026, 3, 10, 14, 0, 0),
         **M2_PROFILE_DEFAULTS[3]),
    dict(brand_id=4, founded_year="2004年", hq="北京",
         positioning="SUBMARINE 潜水艇，地漏/角阀等五金强势；向卫浴全品类延伸。",
         org_structure='{"root":"潜水艇","lead":"电商部","nodes":["经理 · 待补"]}',
         taboos="（待补全）",
         taboo_updated_by=None, taboo_updated_at=None,
         **M2_PROFILE_DEFAULTS[4]),
    dict(brand_id=5, founded_year="2000年", hq="江苏连云港",
         positioning="MICOE 四季沐歌，清洁能源+卫浴；太阳能热水器与卫浴延伸品类。",
         org_structure='{"root":"四季沐歌","lead":"电商中心","nodes":["总监 · 待补"]}',
         taboos="（待补全）",
         taboo_updated_by=None, taboo_updated_at=None,
         **M2_PROFILE_DEFAULTS[5]),
] + [
    dict(
        brand_id=bid,
        founded_year=fy,
        hq=hq,
        positioning=pos,
        org_structure='{"root":"' + name + '","lead":"电商部","nodes":["总监 · 待补"]}',
        taboos="（待补全）",
        taboo_updated_by=None,
        taboo_updated_at=None,
        **JC_PROFILE_DEFAULTS,
    )
    for bid, _key, name, fy, hq, pos in M6_JC_PROFILES
]

METRIC_FLOAT_COLS = {
    "gmv", "gmv_wow", "gmv_yoy", "sales_volume_wow", "sales_volume_yoy",
    "jd_share", "jd_share_wow", "tmall_share", "douyin_share", "taobao_share",
    "channel_growth_jd", "channel_growth_tmall", "channel_growth_douyin", "channel_growth_taobao",
    "gross_margin", "uv_conversion", "ad_rate",
}
METRIC_INT_COLS = {"sales_volume", "sku_count", "p0_gap_count"}

# 底表暂无 · seed 写入 · 前端标注【示范数据】（类目已接 brand_category_monthly.csv）
DEMO_METRICS_BY_KEY = {
    "jomoo": dict(p0_gap_count=2),
    "arrow": dict(p0_gap_count=1),
    "hegii": dict(p0_gap_count=1),
    "submarine": dict(p0_gap_count=2),
    "micoe": dict(p0_gap_count=1),
}

PROFILE_SYNC_FIELDS = (
    "taboos",
    "taboo_updated_by", "taboo_updated_at",
    "founded_year", "hq", "positioning", "org_structure",
)


def _parse_csv_row(row: dict) -> dict:
    out = {"period_type": row.get("period_type") or "monthly", "period_value": row["period_value"]}
    for col in METRIC_FLOAT_COLS:
        if col in row and row[col] not in (None, ""):
            out[col] = float(row[col])
    for col in METRIC_INT_COLS:
        if col in row and row[col] not in (None, ""):
            out[col] = int(float(row[col]))
    return out


def ensure_m2_columns(db):
    """已有库追加 M2 列（幂等 · 仅 MySQL）"""
    if IS_SQLITE:
        return
    insp = inspect(engine)
    if "brand_profiles" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("brand_profiles")}
        if "competitive_landscape" not in cols:
            db.execute(text(
                "ALTER TABLE brand_profiles ADD COLUMN competitive_landscape TEXT NULL COMMENT '竞争格局（M2 可编辑）'"
            ))
            print("已追加 brand_profiles.competitive_landscape")
        if "growth_opportunities" not in cols:
            db.execute(text(
                "ALTER TABLE brand_profiles ADD COLUMN growth_opportunities TEXT NULL COMMENT '增长机会（M2 可编辑）'"
            ))
            print("已追加 brand_profiles.growth_opportunities")

    if "brand_contacts" in insp.get_table_names():
        col = next((c for c in insp.get_columns("brand_contacts") if c["name"] == "role_tag"), None)
        if col and "enum" in str(col.get("type", "")).lower():
            db.execute(text(
                "ALTER TABLE brand_contacts MODIFY COLUMN role_tag VARCHAR(32) "
                "DEFAULT '日常对接' COMMENT '关键人物角色标签，可自定义'"
            ))
            print("已迁移 brand_contacts.role_tag ENUM → VARCHAR(32)")

    if "brand_metrics" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("brand_metrics")}
        if "sales_volume" not in cols and "orders" in cols:
            db.execute(text(
                "ALTER TABLE brand_metrics "
                "CHANGE COLUMN orders sales_volume INT DEFAULT NULL COMMENT '销量', "
                "CHANGE COLUMN orders_wow sales_volume_wow DECIMAL(6,2) DEFAULT NULL COMMENT '销量环比%'"
            ))
            print("已迁移 brand_metrics orders → sales_volume")
        elif "sales_volume" not in cols:
            db.execute(text(
                "ALTER TABLE brand_metrics ADD COLUMN sales_volume INT NULL COMMENT '销量', "
                "ADD COLUMN sales_volume_wow DECIMAL(6,2) NULL COMMENT '销量环比%'"
            ))
            print("已追加 brand_metrics.sales_volume / sales_volume_wow")
        if "sales_volume_yoy" not in cols:
            db.execute(text(
                "ALTER TABLE brand_metrics ADD COLUMN sales_volume_yoy DECIMAL(6,2) NULL COMMENT '销量同比%'"
            ))
            print("已追加 brand_metrics.sales_volume_yoy")
        if "taobao_share" not in cols and "pdd_share" in cols:
            db.execute(text(
                "ALTER TABLE brand_metrics CHANGE COLUMN pdd_share taobao_share DECIMAL(5,2) DEFAULT NULL COMMENT '淘宝市占%'"
            ))
            print("已迁移 brand_metrics pdd_share → taobao_share")
        elif "taobao_share" not in cols:
            db.execute(text(
                "ALTER TABLE brand_metrics ADD COLUMN taobao_share DECIMAL(5,2) DEFAULT NULL COMMENT '淘宝市占%'"
            ))
            print("已追加 brand_metrics.taobao_share")
        if "channel_growth_taobao" not in cols:
            db.execute(text(
                "ALTER TABLE brand_metrics ADD COLUMN channel_growth_taobao DECIMAL(8,2) DEFAULT NULL COMMENT '淘宝渠道增速%'"
            ))
            print("已追加 brand_metrics.channel_growth_taobao")
        # 建材真数同比可达数千 %，DECIMAL(5,2) 上限 999.99 会 1264
        for cg_col, cg_comment in (
            ("channel_growth_jd", None),
            ("channel_growth_tmall", None),
            ("channel_growth_douyin", None),
            ("channel_growth_taobao", "淘宝渠道增速%"),
        ):
            if cg_col not in cols:
                continue
            col_info = next(c for c in insp.get_columns("brand_metrics") if c["name"] == cg_col)
            type_str = str(col_info.get("type", "")).upper()
            if "DECIMAL(5" in type_str or "NUMERIC(5" in type_str:
                comment_sql = f" COMMENT '{cg_comment}'" if cg_comment else ""
                db.execute(text(
                    f"ALTER TABLE brand_metrics MODIFY COLUMN {cg_col} DECIMAL(8,2) DEFAULT NULL{comment_sql}"
                ))
                print(f"已扩宽 brand_metrics.{cg_col} → DECIMAL(8,2)")
    db.commit()


def migrate_legacy_bathroom_strategy(db):
    """卫浴 5 品牌：清掉 M2 时代 seed 短文，改走 Tab2 规则 fallback（与建材一致）"""
    n = 0
    for brand_id in range(1, 6):
        profile = db.query(BrandProfile).filter(BrandProfile.brand_id == brand_id).first()
        if not profile:
            continue
        if profile.competitive_landscape in LEGACY_M2_STRATEGY_COMP:
            profile.competitive_landscape = "（待补全竞争格局分析）"
            n += 1
        if profile.growth_opportunities in LEGACY_M2_STRATEGY_OPP:
            profile.growth_opportunities = "（待补全增长机会）"
            n += 1
    if n:
        db.commit()
        print(f"已迁移卫浴 Tab2 旧 seed 文案 → 占位（{n} 字段），将走规则 fallback")


def sync_brands(db):
    """同步 brands 表为建材十一品牌（id 1～11）"""
    for spec in BRANDS:
        brand = db.query(Brand).filter(Brand.id == spec["id"]).first()
        payload = {k: v for k, v in spec.items() if k != "id"}
        if brand:
            for k, v in payload.items():
                setattr(brand, k, v)
        else:
            db.add(Brand(id=spec["id"], **payload))
    db.commit()
    print("已同步 brands：11 品牌（5 卫浴 + 6 基础建材）")


def sync_profiles(db):
    """同步品牌简介/竞争/机会（覆盖旧厨小占位文案）"""
    for row in PROFILES:
        profile = db.query(BrandProfile).filter(BrandProfile.brand_id == row["brand_id"]).first()
        if profile:
            for field in PROFILE_SYNC_FIELDS:
                if field in row:
                    setattr(profile, field, row[field])
        else:
            db.add(BrandProfile(**row))
    db.commit()
    print("已同步 brand_profiles（11 品牌）")


def reset_legacy_strategy_seed(db):
    """卫浴 5 品牌旧 M2 固定句 → 占位，触发前端规则保底（非用户编辑）"""
    n = 0
    for profile in db.query(BrandProfile).filter(BrandProfile.brand_id <= 5):
        if profile.competitive_landscape in LEGACY_M2_STRATEGY_COMP:
            profile.competitive_landscape = "（待补全竞争格局分析）"
            n += 1
        if profile.growth_opportunities in LEGACY_M2_STRATEGY_OPP:
            profile.growth_opportunities = "（待补全增长机会）"
            n += 1
    if n:
        db.commit()
        print(f"已重置卫浴品牌旧 Tab2 seed 文案 {n} 处 → 占位（走规则保底）")


def apply_demo_metrics(db):
    """为 bi_csv 未覆盖字段写入示范指标（P0 缺口数）"""
    brands_by_key = {b.name_key: b for b in db.query(Brand).all()}
    count = 0
    for name_key, demo in DEMO_METRICS_BY_KEY.items():
        brand = brands_by_key.get(name_key)
        if not brand:
            continue
        payload = dict(demo)
        rows = (
            db.query(BrandMetrics)
            .filter(BrandMetrics.brand_id == brand.id, BrandMetrics.period_type == "monthly")
            .all()
        )
        for row in rows:
            for k, v in payload.items():
                setattr(row, k, v)
            count += 1
    print(f"已写入示范指标字段 {count} 条（P0 缺口 · 前端标注【示范数据】）")


def import_metrics_from_csv(db, csv_path: Path = METRICS_CSV):
    """从 bi_csv 宽表导入 monthly 指标（覆盖旧数据）"""
    if not csv_path.exists():
        print(f"警告：未找到 {csv_path}，跳过 metrics 导入")
        return

    brands_by_key = {b.name_key: b for b in db.query(Brand).all()}
    with csv_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    touched = set()
    for row in rows:
        key = (row.get("name_key") or "").strip().lower()
        brand = brands_by_key.get(key)
        if not brand:
            print(f"警告：未知 name_key={key}，跳过")
            continue
        touched.add(brand.id)

    for brand_id in touched:
        db.query(BrandMetrics).filter(
            BrandMetrics.brand_id == brand_id,
            BrandMetrics.period_type == "monthly",
        ).delete()
        db.query(BrandMetrics).filter(
            BrandMetrics.brand_id == brand_id,
            BrandMetrics.period_type == "weekly",
        ).delete()

    count = 0
    for row in rows:
        key = (row.get("name_key") or "").strip().lower()
        brand = brands_by_key.get(key)
        if not brand:
            continue
        payload = _parse_csv_row(row)
        db.add(BrandMetrics(brand_id=brand.id, **payload))
        count += 1

    print(f"已从 CSV 导入 {count} 条 monthly metrics（{csv_path.name}）")
    db.flush()


def import_category_from_csv(db, csv_path: Path = CATEGORY_CSV):
    """从 brand_category_monthly.csv 合并二级类目 JSON 到 brand_metrics"""
    if not csv_path.exists():
        print(f"警告：未找到 {csv_path}，跳过 category 导入")
        return

    brands_by_key = {b.name_key: b for b in db.query(Brand).all()}
    count = 0
    with csv_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row.get("name_key") or "").strip().lower()
            period = (row.get("period_value") or "").strip()
            brand = brands_by_key.get(key)
            if not brand or not period:
                continue
            metric = (
                db.query(BrandMetrics)
                .filter(
                    BrandMetrics.brand_id == brand.id,
                    BrandMetrics.period_type == "monthly",
                    BrandMetrics.period_value == period,
                )
                .first()
            )
            if not metric:
                continue
            metric.category_distribution = row.get("category_distribution") or None
            metric.category_share = row.get("category_share") or None
            count += 1

    print(f"已从 CSV 合并 {count} 条二级类目（{csv_path.name}）")
    db.flush()


def run_seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_m2_columns(db)
        migrate_legacy_bathroom_strategy(db)
        sync_brands(db)
        sync_profiles(db)

        import_metrics_from_csv(db)
        import_category_from_csv(db)
        apply_demo_metrics(db)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
