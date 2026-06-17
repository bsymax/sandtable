"""
情报模块路由（开开，2026-06-11 合并进主工程 · M2 0616 CSV/分页/briefing 缓存）
- 新闻：列表 / 录入（URL去重）/ 详情 / CSV 批量导入 → intel_news（FK brands）
- 周报：列表 / 提交 / 各品牌最新 → **brand_metrics**（与档案经营底表共用）
- 预警：列表 / 录入 / 更新 / 一键创建紧急拜访 → intel_alerts（FK brands / intel_news / brand_metrics / visits）
- 统计：规则版周报摘要 / 品牌简报（**intel_briefing_cache** 30min TTL）/ 总览
"""

from datetime import date, time, datetime, timedelta
from typing import Optional, List
import csv
import hashlib
import io

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, case, or_

from database import get_db
from deps_auth import AuthUser, filter_brand_query, filter_by_brand_ids, get_current_user_optional, require_brand_id, require_name_key
from models import Brand, Visit, BrandMetrics, IntelNews, IntelAlert, IntelBriefingCache
from schemas import (
    IntelNewsOut, IntelNewsCreate, IntelNewsUpdate,
    IntelWeeklyReportOut, IntelWeeklyReportCreate, IntelWeeklyReportUpdate,
    IntelAlertOut, IntelAlertCreate, IntelAlertUpdate,
    IntelBriefingOut, IntelStatsOut,
    CsvImportRow, CsvImportRequest, CsvImportResult,
    AiBriefingSummaryOut,
)
from llm_service import complete

router = APIRouter()

BRIEFING_CACHE_TTL = 30  # minutes


# ================================================================
#  辅助函数
# ================================================================
def _period_value(week_start: date) -> str:
    iso = week_start.isocalendar()
    return f"{iso[0]}W{iso[1]:02d}"


def _week_label(period_value: str) -> Optional[str]:
    if not period_value:
        return None
    idx = period_value.find("W")
    return period_value[idx:] if idx >= 0 else period_value


def _weekly_metrics_query(db: Session):
    """已填报或含叙事字段的周度 brand_metrics（情报周报视图）"""
    return db.query(BrandMetrics).options(joinedload(BrandMetrics.brand)).filter(
        BrandMetrics.period_type == "weekly",
        or_(
            BrandMetrics.intel_report_status.isnot(None),
            BrandMetrics.competitor_moves.isnot(None),
            BrandMetrics.risk_points.isnot(None),
            BrandMetrics.opportunities.isnot(None),
        ),
    )


def _invalidate_briefing_cache(brand_id: int, db: Session):
    if brand_id:
        db.query(IntelBriefingCache).filter(IntelBriefingCache.brand_id == brand_id).delete()
        db.commit()


def _fmt_news(n):
    return IntelNewsOut(
        id=n.id, brand_id=n.brand_id, brand_name=n.brand.name if n.brand else None,
        title=n.title, summary=n.summary, url=n.url, source=n.source,
        sentiment=n.sentiment, category=n.category, keywords=n.keywords,
        published_at=n.published_at, fetched_at=n.fetched_at, created_at=n.created_at,
    )


def _fmt_weekly(m: BrandMetrics):
    return IntelWeeklyReportOut(
        id=m.id,
        brand_id=m.brand_id,
        brand_name=m.brand.name if m.brand else None,
        week_start=m.week_start,
        week_end=m.week_end,
        week_label=_week_label(m.period_value),
        weekly_gmv=float(m.gmv) if m.gmv is not None else None,
        gmv_change=float(m.gmv_wow) if m.gmv_wow is not None else None,
        competitor_moves=m.competitor_moves,
        inventory_status=m.inventory_status,
        risk_points=m.risk_points,
        opportunities=m.opportunities,
        next_week_plan=m.next_week_plan,
        reporter=m.reporter,
        status=m.intel_report_status or "submitted",
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _apply_weekly_payload(m: BrandMetrics, payload, mark_submitted: bool = False):
    data = payload.model_dump(exclude_unset=True)
    if "weekly_gmv" in data:
        m.gmv = data.pop("weekly_gmv")
    if "gmv_change" in data:
        m.gmv_wow = data.pop("gmv_change")
    if "week_start" in data and data["week_start"]:
        m.period_value = _period_value(data["week_start"])
    for k, v in data.items():
        if k == "week_label":
            continue
        if hasattr(m, k):
            setattr(m, k, v)
    if mark_submitted:
        m.intel_report_status = "submitted"


def _default_alert_category(priority: str, category: Optional[str] = None) -> str:
    if category in ("增长机会", "风险预警"):
        return category
    return "风险预警" if priority == "P0" else "增长机会"


def _briefing_data_for_cache(news_out, alerts_out, latest_weekly, stats: dict) -> dict:
    """JSON 列可序列化（datetime 须 mode='json'）"""
    return {
        "recent_news": [n.model_dump(mode="json") for n in news_out],
        "active_alerts": [a.model_dump(mode="json") for a in alerts_out],
        "latest_weekly": latest_weekly,
        "stats": stats,
    }


def _fmt_alert(a):
    return IntelAlertOut(
        id=a.id, brand_id=a.brand_id, brand_name=a.brand.name if a.brand else None,
        brand_name_key=a.brand.name_key if a.brand else None,
        brand_level=a.brand.level if a.brand else None,
        news_id=a.news_id, weekly_id=a.metrics_id, visit_id=a.visit_id,
        priority=a.priority,
        category=a.category or _default_alert_category(a.priority),
        title=a.title, description=a.description,
        suggestion=a.suggestion, ai_confidence=a.ai_confidence,
        status=a.status, assignee=a.assignee,
        created_at=a.created_at, updated_at=a.updated_at,
    )


def _build_briefing_payload(brand, news, alerts, latest_w):
    news_out = [_fmt_news(n) for n in news]
    alerts_out = [_fmt_alert(a) for a in alerts]
    latest_weekly = {
        "week_label": _week_label(latest_w.period_value) if latest_w else None,
        "weekly_gmv": float(latest_w.gmv) if latest_w and latest_w.gmv is not None else None,
        "gmv_change": float(latest_w.gmv_wow) if latest_w and latest_w.gmv_wow is not None else None,
        "competitor_moves": latest_w.competitor_moves if latest_w else None,
        "risk_points": latest_w.risk_points if latest_w else None,
        "opportunities": latest_w.opportunities if latest_w else None,
        "reporter": latest_w.reporter if latest_w else None,
        "created_at": str(latest_w.created_at) if latest_w else None,
    } if latest_w else None
    return news_out, alerts_out, latest_weekly


# ================================================================
#  新闻
# ================================================================
@router.get("/api/intel/news", response_model=List[IntelNewsOut], tags=["情报-新闻"])
def list_news(
    brand_id: Optional[int] = None,
    sentiment: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    q = db.query(IntelNews).options(joinedload(IntelNews.brand))
    if brand_id:
        require_brand_id(user, brand_id)
        q = q.filter(IntelNews.brand_id == brand_id)
    else:
        q = filter_by_brand_ids(q, IntelNews.brand_id, user)
    if sentiment:
        q = q.filter(IntelNews.sentiment == sentiment)
    if category:
        q = q.filter(IntelNews.category == category)
    rows = q.order_by(desc(IntelNews.published_at)).offset(offset).limit(limit).all()
    return [_fmt_news(r) for r in rows]


@router.post("/api/intel/news", response_model=IntelNewsOut, tags=["情报-新闻"])
def create_news(
    payload: IntelNewsCreate,
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    require_brand_id(user, payload.brand_id)
    fp = None
    if payload.url:
        fp = hashlib.sha256(payload.url.encode()).hexdigest()
        if db.query(IntelNews).filter(IntelNews.url_fingerprint == fp).first():
            raise HTTPException(400, "该新闻URL已存在")
    news = IntelNews(
        brand_id=payload.brand_id, title=payload.title, summary=payload.summary,
        url=payload.url, source=payload.source, sentiment=payload.sentiment or "neutral",
        category=payload.category, keywords=payload.keywords, url_fingerprint=fp,
        published_at=payload.published_at or datetime.now(),
    )
    db.add(news)
    db.commit()
    db.refresh(news)
    if news.brand_id:
        _invalidate_briefing_cache(news.brand_id, db)
    news = db.query(IntelNews).options(joinedload(IntelNews.brand)).filter(IntelNews.id == news.id).first()
    return _fmt_news(news)


@router.put("/api/intel/news/{news_id}", response_model=IntelNewsOut, tags=["情报-新闻"])
def update_news(news_id: int, payload: IntelNewsUpdate, db: Session = Depends(get_db)):
    news = db.query(IntelNews).filter(IntelNews.id == news_id).first()
    if not news:
        raise HTTPException(404, "新闻不存在")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(news, k, v)
    db.commit()
    if news.brand_id:
        _invalidate_briefing_cache(news.brand_id, db)
    news = db.query(IntelNews).options(joinedload(IntelNews.brand)).filter(IntelNews.id == news_id).first()
    return _fmt_news(news)


@router.get("/api/intel/news/{news_id}", response_model=IntelNewsOut, tags=["情报-新闻"])
def get_news(news_id: int, db: Session = Depends(get_db)):
    news = db.query(IntelNews).filter(IntelNews.id == news_id).first()
    if not news:
        raise HTTPException(404, "新闻不存在")
    return _fmt_news(news)


@router.post("/api/intel/news/csv", response_model=CsvImportResult, tags=["情报-新闻"])
def import_news_csv(payload: CsvImportRequest, db: Session = Depends(get_db)):
    result = CsvImportResult(total=len(payload.rows))
    brands = set()
    for i, row in enumerate(payload.rows):
        try:
            if not row.title or not row.title.strip():
                result.errors.append({"row": i + 1, "error": "标题不能为空"})
                result.skipped += 1
                continue
            fp = None
            if row.url:
                fp = hashlib.sha256(row.url.encode()).hexdigest()
                if db.query(IntelNews).filter(IntelNews.url_fingerprint == fp).first():
                    result.errors.append({"row": i + 1, "title": row.title, "error": "URL重复"})
                    result.skipped += 1
                    continue
            pub = None
            if row.published_at:
                try:
                    pub = datetime.fromisoformat(row.published_at.replace("Z", "+00:00"))
                except ValueError:
                    pub = datetime.now()
            news = IntelNews(
                brand_id=row.brand_id,
                title=row.title.strip(),
                summary=row.summary,
                source=row.source or "CSV导入",
                sentiment=row.sentiment or "neutral",
                category=row.category,
                keywords=row.keywords,
                url=row.url,
                url_fingerprint=fp,
                published_at=pub or datetime.now(),
            )
            db.add(news)
            db.flush()
            result.imported_ids.append(news.id)
            result.success += 1
            if row.brand_id:
                brands.add(row.brand_id)
        except Exception as e:
            result.errors.append({"row": i + 1, "title": row.title if row else "?", "error": str(e)})
            result.skipped += 1
    db.commit()
    for bid in brands:
        _invalidate_briefing_cache(bid, db)
    return result


@router.post("/api/intel/news/csv/upload", response_model=CsvImportResult, tags=["情报-新闻"])
async def upload_news_csv(
    file: UploadFile = File(...),
    brand_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for rd in reader:
        raw_bid = rd.get("brand_id", "").strip()
        if brand_id and not raw_bid:
            bid = brand_id
        elif raw_bid:
            bid = int(raw_bid)
        else:
            bid = None
        rows.append(CsvImportRow(
            brand_id=bid,
            title=rd.get("title", ""),
            summary=rd.get("summary", ""),
            source=rd.get("source", "CSV导入"),
            sentiment=rd.get("sentiment", "neutral"),
            category=rd.get("category", ""),
            keywords=rd.get("keywords", ""),
            url=rd.get("url", ""),
            published_at=rd.get("published_at", ""),
        ))
    return import_news_csv(CsvImportRequest(rows=rows), db)


@router.get("/api/intel/news/csv/template", tags=["情报-新闻"])
def download_csv_template():
    return {
        "template": (
            "brand_id,title,summary,source,sentiment,category,keywords,url,published_at\n"
            "1,示例新闻标题,摘要内容,行业情报,neutral,行业,关键词,https://example.com/1,2026-06-10T10:00:00\n"
        )
    }


# ================================================================
#  周报（读写 brand_metrics，与档案经营底表共用）
# ================================================================
@router.get("/api/intel/weekly", response_model=List[IntelWeeklyReportOut], tags=["情报-周报"])
def list_weekly(
    brand_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    q = _weekly_metrics_query(db)
    if brand_id:
        require_brand_id(user, brand_id)
        q = q.filter(BrandMetrics.brand_id == brand_id)
    else:
        q = filter_by_brand_ids(q, BrandMetrics.brand_id, user)
    rows = q.order_by(desc(BrandMetrics.week_start), desc(BrandMetrics.id)).offset(offset).limit(limit).all()
    return [_fmt_weekly(r) for r in rows]


@router.post("/api/intel/weekly", response_model=IntelWeeklyReportOut, tags=["情报-周报"])
def create_weekly(payload: IntelWeeklyReportCreate, db: Session = Depends(get_db)):
    if not db.query(Brand).filter(Brand.id == payload.brand_id).first():
        raise HTTPException(404, "品牌不存在")
    pv = _period_value(payload.week_start)
    m = db.query(BrandMetrics).filter(
        BrandMetrics.brand_id == payload.brand_id,
        BrandMetrics.period_type == "weekly",
        BrandMetrics.period_value == pv,
    ).first()
    if m and m.intel_report_status == "submitted":
        raise HTTPException(400, "该品牌本周报已存在")
    if not m:
        m = BrandMetrics(brand_id=payload.brand_id, period_type="weekly", period_value=pv)
        db.add(m)
    _apply_weekly_payload(m, payload, mark_submitted=True)
    db.commit()
    db.refresh(m)
    _invalidate_briefing_cache(payload.brand_id, db)
    m = db.query(BrandMetrics).options(joinedload(BrandMetrics.brand)).filter(BrandMetrics.id == m.id).first()
    return _fmt_weekly(m)


@router.put("/api/intel/weekly/{weekly_id}", response_model=IntelWeeklyReportOut, tags=["情报-周报"])
def update_weekly(weekly_id: int, payload: IntelWeeklyReportUpdate, db: Session = Depends(get_db)):
    m = db.query(BrandMetrics).filter(
        BrandMetrics.id == weekly_id,
        BrandMetrics.period_type == "weekly",
    ).first()
    if not m:
        raise HTTPException(404, "周报不存在")
    _apply_weekly_payload(m, payload)
    db.commit()
    _invalidate_briefing_cache(m.brand_id, db)
    m = db.query(BrandMetrics).options(joinedload(BrandMetrics.brand)).filter(BrandMetrics.id == weekly_id).first()
    return _fmt_weekly(m)


@router.get("/api/intel/weekly/latest", response_model=List[IntelWeeklyReportOut], tags=["情报-周报"])
def latest_weekly(
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    q = db.query(Brand).filter(Brand.status == "active")
    brands = filter_brand_query(q, user).all()
    result = []
    for b in brands:
        latest = _weekly_metrics_query(db).filter(
            BrandMetrics.brand_id == b.id
        ).order_by(desc(BrandMetrics.week_start), desc(BrandMetrics.id)).first()
        if latest:
            result.append(_fmt_weekly(latest))
    return result


# ================================================================
#  预警
# ================================================================
@router.get("/api/intel/alerts", response_model=List[IntelAlertOut], tags=["情报-预警"])
def list_alerts(
    brand_id: Optional[int] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    q = db.query(IntelAlert).options(joinedload(IntelAlert.brand))
    if brand_id:
        require_brand_id(user, brand_id)
        q = q.filter(IntelAlert.brand_id == brand_id)
    else:
        q = filter_by_brand_ids(q, IntelAlert.brand_id, user)
    if priority:
        q = q.filter(IntelAlert.priority == priority)
    if category:
        q = q.filter(IntelAlert.category == category)
    if status:
        q = q.filter(IntelAlert.status == status)
    rows = q.order_by(
        case((IntelAlert.priority == "P0", 0), (IntelAlert.priority == "P1", 1), else_=2),
        desc(IntelAlert.created_at),
    ).offset(offset).limit(limit).all()
    return [_fmt_alert(a) for a in rows]


@router.post("/api/intel/alerts", response_model=IntelAlertOut, tags=["情报-预警"])
def create_alert(payload: IntelAlertCreate, db: Session = Depends(get_db)):
    alert = IntelAlert(
        brand_id=payload.brand_id, news_id=payload.news_id,
        priority=payload.priority,
        category=_default_alert_category(payload.priority, payload.category),
        title=payload.title,
        description=payload.description, suggestion=payload.suggestion,
        assignee=payload.assignee, status="pending",
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    if alert.brand_id:
        _invalidate_briefing_cache(alert.brand_id, db)
    alert = db.query(IntelAlert).options(joinedload(IntelAlert.brand)).filter(IntelAlert.id == alert.id).first()
    return _fmt_alert(alert)


@router.put("/api/intel/alerts/{alert_id}", response_model=IntelAlertOut, tags=["情报-预警"])
def update_alert(alert_id: int, payload: IntelAlertUpdate, db: Session = Depends(get_db)):
    alert = db.query(IntelAlert).filter(IntelAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(404, "预警不存在")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(alert, k, v)
    db.commit()
    db.refresh(alert)
    if alert.brand_id:
        _invalidate_briefing_cache(alert.brand_id, db)
    alert = db.query(IntelAlert).options(joinedload(IntelAlert.brand)).filter(IntelAlert.id == alert.id).first()
    return _fmt_alert(alert)


@router.post("/api/intel/alerts/{alert_id}/create-visit", tags=["情报-预警"])
def create_visit_from_alert(alert_id: int, db: Session = Depends(get_db)):
    """从预警一键创建紧急拜访（写公共表 visits，与拜访模块联动）"""
    alert = db.query(IntelAlert).options(joinedload(IntelAlert.brand)).filter(IntelAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(404, "预警不存在")
    if not alert.brand_id:
        raise HTTPException(400, "预警未关联品牌")

    visit = Visit(
        brand_id=alert.brand_id,
        visit_date=date.today() + timedelta(days=1),
        visit_time=time(14, 0),
        visit_type="urgent",
        purpose=f"[预警] {alert.title}",
        notes=alert.suggestion or alert.description,
        status="scheduled",
    )
    db.add(visit)
    db.flush()
    alert.visit_id = visit.id
    alert.status = "linked"
    db.commit()
    db.refresh(visit)
    return {
        "id": visit.id, "brand_id": visit.brand_id, "visit_date": str(visit.visit_date),
        "brand_name": alert.brand.name if alert.brand else None, "status": visit.status,
    }


# ================================================================
#  周报摘要（规则版）
# ================================================================
@router.get("/api/intel/weekly-summary", tags=["情报-统计"])
def weekly_summary(db: Session = Depends(get_db)):
    """规则版周报摘要：本周新增情报N条（P0×a/P1×b），主要涉及{品牌}，最高优先级：{标题}"""
    one_week_ago = datetime.now() - timedelta(days=7)
    new_alerts = db.query(IntelAlert).filter(IntelAlert.created_at >= one_week_ago).order_by(
        case((IntelAlert.priority == "P0", 0), (IntelAlert.priority == "P1", 1), else_=2)
    ).all()
    new_news = db.query(IntelNews).filter(IntelNews.created_at >= one_week_ago).all()

    total = len(new_alerts) + len(new_news)
    p0 = sum(1 for a in new_alerts if a.priority == "P0")
    p1 = sum(1 for a in new_alerts if a.priority == "P1")

    brand_ids = set()
    for a in new_alerts:
        if a.brand_id:
            brand_ids.add(a.brand_id)
    for n in new_news:
        if n.brand_id:
            brand_ids.add(n.brand_id)
    brand_names = []
    for bid in brand_ids:
        b = db.query(Brand).filter(Brand.id == bid).first()
        if b:
            brand_names.append(b.name)

    top = new_alerts[0] if new_alerts else None
    brand_str = "、".join(brand_names[:3]) if brand_names else "全行业"
    if len(brand_names) > 3:
        brand_str += f"等{len(brand_names)}个品牌"

    parts = [f"本周新增情报 {total} 条"]
    if p0 or p1:
        parts.append(f"（P0×{p0}/P1×{p1}）")
    parts.append(f"，主要涉及 {brand_str}")
    if top:
        parts.append(f"，最高优先级事项：{top.title}")
    else:
        parts.append("，暂无高优预警")

    return {
        "summary": "".join(parts),
        "week_start": (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d"),
        "week_end": datetime.now().strftime("%Y-%m-%d"),
        "total": total, "p0_count": p0, "p1_count": p1,
        "brands": brand_names,
        "top_alert": {"priority": top.priority, "title": top.title} if top else None,
    }


# ================================================================
#  简报 & 统计
# ================================================================
@router.get("/api/intel/briefing/{brand_key}", response_model=IntelBriefingOut, tags=["情报-简报"])
def get_brand_briefing(
    brand_key: str,
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    require_name_key(user, brand_key)
    brand = db.query(Brand).filter(Brand.name_key == brand_key).first()
    if not brand:
        raise HTTPException(404, "品牌不存在")

    cached = None
    try:
        cached = db.query(IntelBriefingCache).filter(IntelBriefingCache.brand_id == brand.id).first()
        if cached and cached.expires_at and cached.expires_at > datetime.now() and cached.briefing_data:
            d = cached.briefing_data
            return IntelBriefingOut(
                brand_id=brand.id, brand_name=brand.name, brand_level=brand.level,
                recent_news=d.get("recent_news", []),
                active_alerts=d.get("active_alerts", []),
                latest_weekly=d.get("latest_weekly"),
                stats=d.get("stats", {}),
                cached=True,
            )
    except Exception:
        db.rollback()

    two_weeks_ago = datetime.now() - timedelta(days=14)
    news = db.query(IntelNews).options(joinedload(IntelNews.brand)).filter(
        IntelNews.brand_id == brand.id,
        IntelNews.published_at >= two_weeks_ago,
    ).order_by(desc(IntelNews.published_at)).limit(10).all()

    alerts = db.query(IntelAlert).options(joinedload(IntelAlert.brand)).filter(
        IntelAlert.brand_id == brand.id,
        IntelAlert.status.in_(["pending", "confirmed"]),
    ).order_by(case((IntelAlert.priority == "P0", 0), (IntelAlert.priority == "P1", 1), else_=2)).all()

    latest_w = _weekly_metrics_query(db).filter(
        BrandMetrics.brand_id == brand.id
    ).order_by(desc(BrandMetrics.week_start), desc(BrandMetrics.id)).first()

    news_out, alerts_out, latest_weekly = _build_briefing_payload(brand, news, alerts, latest_w)
    briefing_data = _briefing_data_for_cache(
        news_out,
        alerts_out,
        latest_weekly,
        {"total_news": len(news), "active_alerts": len(alerts)},
    )
    expires_at = datetime.now() + timedelta(minutes=BRIEFING_CACHE_TTL)
    try:
        if cached:
            cached.briefing_data = briefing_data
            cached.generated_at = datetime.now()
            cached.expires_at = expires_at
            cached.updated_at = datetime.now()
        else:
            db.add(IntelBriefingCache(
                brand_id=brand.id,
                briefing_data=briefing_data,
                generated_at=datetime.now(),
                expires_at=expires_at,
            ))
        db.commit()
    except Exception:
        db.rollback()

    return IntelBriefingOut(
        brand_id=brand.id, brand_name=brand.name, brand_level=brand.level,
        recent_news=news_out,
        active_alerts=alerts_out,
        latest_weekly=latest_weekly,
        stats=briefing_data["stats"],
        cached=False,
    )


@router.post("/api/intel/briefing/{brand_key}/refresh", tags=["情报-简报"])
def refresh_briefing(brand_key: str, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.name_key == brand_key).first()
    if not brand:
        raise HTTPException(404, "品牌不存在")
    _invalidate_briefing_cache(brand.id, db)
    return {"message": f"品牌 {brand.name} 简报缓存已清除", "brand_id": brand.id}


@router.post("/api/intel/briefing/{brand_key}/ai/summary", response_model=AiBriefingSummaryOut, tags=["情报-简报"])
async def ai_briefing_summary(
    brand_key: str,
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """Feed/briefing LLM 摘要槽位 · 失败降级规则句"""
    require_name_key(user, brand_key)
    brand = db.query(Brand).filter(Brand.name_key == brand_key).first()
    if not brand:
        raise HTTPException(404, "品牌不存在")
    alerts = db.query(IntelAlert).filter(
        IntelAlert.brand_id == brand.id,
        IntelAlert.status.in_(["pending", "confirmed"]),
    ).all()
    p0 = [a for a in alerts if a.priority == "P0"]
    fallback = f"【{brand.name}】当前 {len(alerts)} 条活跃预警"
    if p0:
        fallback += f"，其中 P0：{p0[0].title}"
    fallback += "（规则版 · LLM 未启用）"
    ctx = fallback.replace("（规则版 · LLM 未启用）", "") + "\n请用 2 句话写采销行动建议。"
    text = await complete("品牌情报简报助手，简体中文。", ctx, max_tokens=200)
    if text:
        return AiBriefingSummaryOut(source="llm", brand_key=brand_key, summary=text.strip())
    return AiBriefingSummaryOut(source="fallback", brand_key=brand_key, summary=fallback)


@router.get("/api/intel/stats", response_model=IntelStatsOut, tags=["情报-统计"])
def intel_stats(
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    one_week_ago = datetime.now() - timedelta(days=7)
    news_q = db.query(func.count(IntelNews.id)).filter(IntelNews.created_at >= one_week_ago)
    alert_q = db.query(IntelAlert).filter(IntelAlert.status != "closed")
    if user and not user.is_admin:
        if not user.brand_ids:
            return IntelStatsOut(total_news_week=0, total_alerts=0, p0_count=0, p1_count=0, p2_count=0, p3_count=0)
        news_q = news_q.filter(IntelNews.brand_id.in_(user.brand_ids))
        alert_q = alert_q.filter(IntelAlert.brand_id.in_(user.brand_ids))
    total_news = news_q.scalar() or 0
    alerts = alert_q.all()
    p0 = sum(1 for a in alerts if a.priority == "P0")
    p1 = sum(1 for a in alerts if a.priority == "P1")
    p2 = sum(1 for a in alerts if a.priority == "P2")
    p3 = sum(1 for a in alerts if a.priority == "P3")
    return IntelStatsOut(
        total_news_week=total_news, total_alerts=p0 + p1 + p2 + p3,
        p0_count=p0, p1_count=p1, p2_count=p2, p3_count=p3,
    )
