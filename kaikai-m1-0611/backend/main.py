"""
品牌情报平台 API · 情报席（开开）
启动: python3 main.py  端口 8002
"""
from datetime import date, time, datetime, timedelta
from typing import Optional, List
import hashlib

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, case

from config import CORS_ORIGINS, SERVER_HOST, SERVER_PORT
from database import get_db, engine
from models import Base, Brand, Visit
from models import IntelNews, IntelWeeklyReport, IntelAlert
from schemas import (
    BrandBrief,
    IntelNewsOut, IntelNewsCreate,
    IntelWeeklyReportOut, IntelWeeklyReportCreate,
    IntelAlertOut, IntelAlertCreate, IntelAlertUpdate,
    IntelBriefingOut, IntelStatsOut,
    ApiResponse,
)

# ---- 建表 ----
Base.metadata.create_all(bind=engine)

# ---- FastAPI ----
app = FastAPI(
    title="品牌沙盘 M1 · 品牌情报平台 API",
    version="1.0.0",
    description="外部新闻 + 内部周报 + AI预警 · 与拜访助手联动",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================================================================
#  品牌（共享，只读）
# ================================================================
@app.get("/api/brands", response_model=List[BrandBrief], tags=["品牌"])
def list_brands(db: Session = Depends(get_db)):
    return db.query(Brand).filter(Brand.status == "active").order_by(
        case((Brand.level=="S",0),(Brand.level=="A",1),(Brand.level=="B",2),else_=3)
    ).all()


# ================================================================
#  新闻
# ================================================================
@app.get("/api/intel/news", response_model=List[IntelNewsOut], tags=["情报-新闻"])
def list_news(
    brand_id: Optional[int] = None,
    sentiment: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(IntelNews)
    if brand_id: q = q.filter(IntelNews.brand_id == brand_id)
    if sentiment: q = q.filter(IntelNews.sentiment == sentiment)
    if category: q = q.filter(IntelNews.category == category)
    return [_fmt_news(r) for r in q.order_by(desc(IntelNews.published_at)).limit(limit).all()]


@app.post("/api/intel/news", response_model=IntelNewsOut, tags=["情报-新闻"])
def create_news(payload: IntelNewsCreate, db: Session = Depends(get_db)):
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
    db.add(news); db.commit(); db.refresh(news)
    return _fmt_news(news)


@app.get("/api/intel/news/{news_id}", response_model=IntelNewsOut, tags=["情报-新闻"])
def get_news(news_id: int, db: Session = Depends(get_db)):
    news = db.query(IntelNews).filter(IntelNews.id == news_id).first()
    if not news: raise HTTPException(404, "新闻不存在")
    return _fmt_news(news)


# ================================================================
#  周报
# ================================================================
@app.get("/api/intel/weekly", response_model=List[IntelWeeklyReportOut], tags=["情报-周报"])
def list_weekly(brand_id: Optional[int] = None, limit: int = 20, db: Session = Depends(get_db)):
    q = db.query(IntelWeeklyReport)
    if brand_id: q = q.filter(IntelWeeklyReport.brand_id == brand_id)
    return [_fmt_weekly(r) for r in q.order_by(desc(IntelWeeklyReport.week_start)).limit(limit).all()]


@app.post("/api/intel/weekly", response_model=IntelWeeklyReportOut, tags=["情报-周报"])
def create_weekly(payload: IntelWeeklyReportCreate, db: Session = Depends(get_db)):
    if not db.query(Brand).filter(Brand.id == payload.brand_id).first():
        raise HTTPException(404, "品牌不存在")
    if db.query(IntelWeeklyReport).filter(
        IntelWeeklyReport.brand_id == payload.brand_id,
        IntelWeeklyReport.week_start == payload.week_start,
    ).first():
        raise HTTPException(400, "该品牌本周报已存在")
    r = IntelWeeklyReport(**payload.dict()); r.status = "submitted"
    db.add(r); db.commit(); db.refresh(r)
    return _fmt_weekly(r)


@app.get("/api/intel/weekly/latest", response_model=List[IntelWeeklyReportOut], tags=["情报-周报"])
def latest_weekly(db: Session = Depends(get_db)):
    brands = db.query(Brand).filter(Brand.status == "active").all()
    result = []
    for b in brands:
        latest = db.query(IntelWeeklyReport).filter(
            IntelWeeklyReport.brand_id == b.id
        ).order_by(desc(IntelWeeklyReport.week_start)).first()
        if latest: result.append(_fmt_weekly(latest))
    return result


# ================================================================
#  预警
# ================================================================
@app.get("/api/intel/alerts", response_model=List[IntelAlertOut], tags=["情报-预警"])
def list_alerts(
    brand_id: Optional[int] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(IntelAlert)
    if brand_id: q = q.filter(IntelAlert.brand_id == brand_id)
    if priority: q = q.filter(IntelAlert.priority == priority)
    if status: q = q.filter(IntelAlert.status == status)
    return [_fmt_alert(a) for a in q.order_by(
        case((IntelAlert.priority=="P0",0),(IntelAlert.priority=="P1",1),else_=2),
        desc(IntelAlert.created_at),
    ).limit(limit).all()]


@app.post("/api/intel/alerts", response_model=IntelAlertOut, tags=["情报-预警"])
def create_alert(payload: IntelAlertCreate, db: Session = Depends(get_db)):
    alert = IntelAlert(
        brand_id=payload.brand_id, news_id=payload.news_id,
        priority=payload.priority, title=payload.title,
        description=payload.description, suggestion=payload.suggestion,
        assignee=payload.assignee, status="pending",
    )
    db.add(alert); db.commit(); db.refresh(alert)
    return _fmt_alert(alert)


@app.put("/api/intel/alerts/{alert_id}", response_model=IntelAlertOut, tags=["情报-预警"])
def update_alert(alert_id: int, payload: IntelAlertUpdate, db: Session = Depends(get_db)):
    alert = db.query(IntelAlert).filter(IntelAlert.id == alert_id).first()
    if not alert: raise HTTPException(404, "预警不存在")
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(alert, k, v)
    db.commit(); db.refresh(alert)
    return _fmt_alert(alert)


@app.post("/api/intel/alerts/{alert_id}/create-visit", tags=["情报-预警"])
def create_visit_from_alert(alert_id: int, db: Session = Depends(get_db)):
    """从预警一键创建紧急拜访"""
    alert = db.query(IntelAlert).filter(IntelAlert.id == alert_id).first()
    if not alert: raise HTTPException(404, "预警不存在")
    if not alert.brand_id: raise HTTPException(400, "预警未关联品牌")

    visit = Visit(
        brand_id=alert.brand_id,
        visit_date=date.today() + timedelta(days=1),
        visit_time=time(14, 0),
        visit_type="urgent",
        purpose=f"[预警] {alert.title}",
        notes=alert.suggestion or alert.description,
        status="scheduled",
    )
    db.add(visit); db.flush()
    alert.visit_id = visit.id; alert.status = "linked"
    db.commit(); db.refresh(visit)
    return {
        "id": visit.id, "brand_id": visit.brand_id, "visit_date": str(visit.visit_date),
        "brand_name": alert.brand.name if alert.brand else None, "status": visit.status,
    }


# ================================================================
#  周报摘要（规则版）
# ================================================================
@app.get("/api/intel/weekly-summary", tags=["情报-统计"])
def weekly_summary(db: Session = Depends(get_db)):
    """规则版周报摘要：本周新增情报N条（P0×a/P1×b），主要涉及{品牌}，最高优先级：{标题}"""
    one_week_ago = datetime.now() - timedelta(days=7)
    new_alerts = db.query(IntelAlert).filter(IntelAlert.created_at >= one_week_ago).order_by(
        case((IntelAlert.priority=="P0",0),(IntelAlert.priority=="P1",1),else_=2)
    ).all()
    new_news = db.query(IntelNews).filter(IntelNews.created_at >= one_week_ago).all()

    total = len(new_alerts) + len(new_news)
    p0 = sum(1 for a in new_alerts if a.priority == "P0")
    p1 = sum(1 for a in new_alerts if a.priority == "P1")

    brand_ids = set()
    for a in new_alerts:
        if a.brand_id: brand_ids.add(a.brand_id)
    for n in new_news:
        if n.brand_id: brand_ids.add(n.brand_id)
    brand_names = []
    for bid in brand_ids:
        b = db.query(Brand).filter(Brand.id == bid).first()
        if b: brand_names.append(b.name)

    top = new_alerts[0] if new_alerts else None
    brand_str = "、".join(brand_names[:3]) if brand_names else "全行业"
    if len(brand_names) > 3: brand_str += f"等{len(brand_names)}个品牌"

    parts = [f"本周新增情报 {total} 条"]
    if p0 or p1: parts.append(f"（P0×{p0}/P1×{p1}）")
    parts.append(f"，主要涉及 {brand_str}")
    if top: parts.append(f"，最高优先级事项：{top.title}")
    else: parts.append("，暂无高优预警")

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
@app.get("/api/intel/briefing/{brand_key}", response_model=IntelBriefingOut, tags=["情报-简报"])
def get_brand_briefing(brand_key: str, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.name_key == brand_key).first()
    if not brand: raise HTTPException(404, "品牌不存在")

    two_weeks_ago = datetime.now() - timedelta(days=14)
    news = db.query(IntelNews).filter(
        IntelNews.brand_id == brand.id,
        IntelNews.published_at >= two_weeks_ago,
    ).order_by(desc(IntelNews.published_at)).limit(10).all()

    alerts = db.query(IntelAlert).filter(
        IntelAlert.brand_id == brand.id,
        IntelAlert.status.in_(["pending", "confirmed"]),
    ).order_by(case((IntelAlert.priority=="P0",0),(IntelAlert.priority=="P1",1),else_=2)).all()

    latest_w = db.query(IntelWeeklyReport).filter(
        IntelWeeklyReport.brand_id == brand.id
    ).order_by(desc(IntelWeeklyReport.week_start)).first()

    return IntelBriefingOut(
        brand_id=brand.id, brand_name=brand.name, brand_level=brand.level,
        recent_news=[_fmt_news(n) for n in news],
        active_alerts=[_fmt_alert(a) for a in alerts],
        latest_weekly={
            "week_label": latest_w.week_label, "weekly_gmv": latest_w.weekly_gmv,
            "gmv_change": latest_w.gmv_change, "competitor_moves": latest_w.competitor_moves,
            "risk_points": latest_w.risk_points, "opportunities": latest_w.opportunities,
            "reporter": latest_w.reporter, "created_at": str(latest_w.created_at),
        } if latest_w else None,
        stats={"total_news": len(news), "active_alerts": len(alerts)},
    )


@app.get("/api/intel/stats", response_model=IntelStatsOut, tags=["情报-统计"])
def intel_stats(db: Session = Depends(get_db)):
    one_week_ago = datetime.now() - timedelta(days=7)
    total_news = db.query(func.count(IntelNews.id)).filter(IntelNews.created_at >= one_week_ago).scalar() or 0
    p0 = db.query(func.count(IntelAlert.id)).filter(IntelAlert.priority=="P0",IntelAlert.status!="closed").scalar() or 0
    p1 = db.query(func.count(IntelAlert.id)).filter(IntelAlert.priority=="P1",IntelAlert.status!="closed").scalar() or 0
    p2 = db.query(func.count(IntelAlert.id)).filter(IntelAlert.priority=="P2",IntelAlert.status!="closed").scalar() or 0
    p3 = db.query(func.count(IntelAlert.id)).filter(IntelAlert.priority=="P3",IntelAlert.status!="closed").scalar() or 0
    return IntelStatsOut(total_news_week=total_news,total_alerts=p0+p1+p2+p3,p0_count=p0,p1_count=p1,p2_count=p2,p3_count=p3)


# ================================================================
#  辅助函数
# ================================================================
def _fmt_news(n):
    return IntelNewsOut(
        id=n.id, brand_id=n.brand_id, brand_name=n.brand.name if n.brand else None,
        title=n.title, summary=n.summary, url=n.url, source=n.source,
        sentiment=n.sentiment, category=n.category, keywords=n.keywords,
        published_at=n.published_at, fetched_at=n.fetched_at, created_at=n.created_at,
    )

def _fmt_weekly(r):
    return IntelWeeklyReportOut(
        id=r.id, brand_id=r.brand_id, brand_name=r.brand.name if r.brand else None,
        week_start=r.week_start, week_end=r.week_end, week_label=r.week_label,
        weekly_gmv=r.weekly_gmv, gmv_change=r.gmv_change,
        competitor_moves=r.competitor_moves, inventory_status=r.inventory_status,
        risk_points=r.risk_points, opportunities=r.opportunities,
        next_week_plan=r.next_week_plan, reporter=r.reporter,
        status=r.status, created_at=r.created_at, updated_at=r.updated_at,
    )

def _fmt_alert(a):
    return IntelAlertOut(
        id=a.id, brand_id=a.brand_id, brand_name=a.brand.name if a.brand else None,
        brand_level=a.brand.level if a.brand else None,
        news_id=a.news_id, weekly_id=a.weekly_id, visit_id=a.visit_id,
        priority=a.priority, title=a.title, description=a.description,
        suggestion=a.suggestion, ai_confidence=a.ai_confidence,
        status=a.status, assignee=a.assignee,
        created_at=a.created_at, updated_at=a.updated_at,
    )


# ---- 入口 ----
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=SERVER_HOST, port=SERVER_PORT, reload=True)
