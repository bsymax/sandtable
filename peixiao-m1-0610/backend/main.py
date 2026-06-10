"""
FastAPI 主应用 —— 智能拜访助手 API
启动命令: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

from datetime import date, time, datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, case

from config import CORS_ORIGINS, SERVER_HOST, SERVER_PORT
from database import get_db, engine
from models import Base, Brand, BrandContact, Visit, VisitAttendee, VisitRecord, Commitment, Todo
from schemas import (
    BrandOut, BrandBrief, ContactOut,
    VisitCreate, VisitOut, VisitUpdate, VisitAttendeeOut,
    RecordCreate, RecordOut,
    CommitmentOut, CommitmentUpdate,
    TodoOut, TodoUpdate,
    HealthItem, ApiResponse,
)

# ---------- 创建表 ----------
Base.metadata.create_all(bind=engine)

# ---------- FastAPI 实例 ----------
app = FastAPI(
    title="品牌沙盘 M1 · 智能拜访助手 API",
    version="1.0.0",
    description="拜访安排、记录、承诺、待办全链路 API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================================================================
#  品牌
# ================================================================
@app.get("/api/brands", response_model=List[BrandBrief], tags=["品牌"])
def list_brands(db: Session = Depends(get_db)):
    """品牌下拉列表"""
    return db.query(Brand).filter(Brand.status == "active").order_by(
        case(
            (Brand.level == "S", 0),
            (Brand.level == "A", 1),
            (Brand.level == "B", 2),
            else_=3,
        )
    ).all()


@app.get("/api/brands/detail", response_model=List[BrandOut], tags=["品牌"])
def list_brands_detail(db: Session = Depends(get_db)):
    """品牌列表（含完整度、温度等）"""
    return db.query(Brand).filter(Brand.status == "active").order_by(Brand.id).all()


@app.get("/api/brands/{name_key}", response_model=BrandOut, tags=["品牌"])
def get_brand(name_key: str, db: Session = Depends(get_db)):
    """按 name_key 获取品牌详情"""
    brand = db.query(Brand).filter(Brand.name_key == name_key, Brand.status == "active").first()
    if not brand:
        raise HTTPException(404, "品牌不存在")
    return brand


# ================================================================
#  联系人
# ================================================================
@app.get("/api/brands/{brand_id}/contacts", response_model=List[ContactOut], tags=["联系人"])
def list_contacts(brand_id: int, db: Session = Depends(get_db)):
    return db.query(BrandContact).filter(
        BrandContact.brand_id == brand_id,
        BrandContact.is_active == True,
    ).all()


# ================================================================
#  拜访安排
# ================================================================
@app.post("/api/visits", response_model=VisitOut, tags=["拜访"])
def create_visit(payload: VisitCreate, db: Session = Depends(get_db)):
    """安排新拜访"""
    # 校验品牌存在
    brand = db.query(Brand).filter(Brand.id == payload.brand_id).first()
    if not brand:
        raise HTTPException(404, "品牌不存在")

    visit = Visit(
        brand_id=payload.brand_id,
        visit_date=payload.visit_date,
        visit_time=payload.visit_time or time(14, 0),
        visit_type=payload.visit_type,
        purpose=payload.purpose,
        notes=payload.notes,
        status="scheduled",
    )
    db.add(visit)
    db.flush()  # 获取 visit.id

    # 添加参与人员
    for name in payload.attendee_names:
        if name.strip():
            db.add(VisitAttendee(visit_id=visit.id, name=name.strip(), role="brand"))

    db.commit()
    db.refresh(visit)

    return _format_visit(visit, brand)


@app.get("/api/visits", response_model=List[VisitOut], tags=["拜访"])
def list_visits(
    status: Optional[str] = Query(None, description="scheduled | completed | cancelled"),
    brand_id: Optional[int] = None,
    month: Optional[str] = Query(None, description="月份，如 2026-06"),
    db: Session = Depends(get_db),
):
    """拜访列表（支持筛选）"""
    q = db.query(Visit)

    if status:
        q = q.filter(Visit.status == status)
    if brand_id:
        q = q.filter(Visit.brand_id == brand_id)
    if month:
        q = q.filter(func.date_format(Visit.visit_date, "%Y-%m") == month)

    q = q.order_by(desc(Visit.visit_date))
    visits = q.all()

    # enrich brand info
    result = []
    for v in visits:
        result.append(_format_visit(v, v.brand))
    return result


@app.get("/api/visits/{visit_id}", response_model=VisitOut, tags=["拜访"])
def get_visit(visit_id: int, db: Session = Depends(get_db)):
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(404, "拜访不存在")
    return _format_visit(visit, visit.brand)


@app.put("/api/visits/{visit_id}", response_model=VisitOut, tags=["拜访"])
def update_visit(visit_id: int, payload: VisitUpdate, db: Session = Depends(get_db)):
    """更新拜访状态 / 时间"""
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(404, "拜访不存在")

    update_data = payload.dict(exclude_unset=True)
    for k, v in update_data.items():
        setattr(visit, k, v)
    db.commit()
    db.refresh(visit)
    return _format_visit(visit, visit.brand)


@app.delete("/api/visits/{visit_id}", response_model=ApiResponse, tags=["拜访"])
def delete_visit(visit_id: int, db: Session = Depends(get_db)):
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(404, "拜访不存在")
    db.delete(visit)
    db.commit()
    return ApiResponse(message="拜访已删除")


# ================================================================
#  拜访记录
# ================================================================
@app.post("/api/records", response_model=RecordOut, tags=["拜访记录"])
def create_record(payload: RecordCreate, db: Session = Depends(get_db)):
    """保存拜访后记录，自动生成待办"""
    # 校验拜访存在
    visit = db.query(Visit).filter(Visit.id == payload.visit_id).first()
    if not visit:
        raise HTTPException(404, "拜访不存在")

    # 检查是否已有记录
    existing = db.query(VisitRecord).filter(VisitRecord.visit_id == payload.visit_id).first()
    if existing:
        raise HTTPException(400, "该拜访已有记录，请使用更新接口")

    record = VisitRecord(
        visit_id=payload.visit_id,
        participants=payload.participants,
        topics=payload.topics,
        commitments_raw=payload.commitments_raw,
        undone_items=payload.undone_items,
        relation_change=payload.relation_change,
        next_visit_date=payload.next_visit_date,
    )
    db.add(record)
    db.flush()

    # 更新拜访状态为 completed
    visit.status = "completed"
    visit.record_id = record.id

    # 自动创建待办
    for td in payload.todos:
        db.add(Todo(
            record_id=record.id,
            visit_id=payload.visit_id,
            priority=td.get("priority", "P2"),
            title=td.get("title", ""),
            deadline=_parse_date(td.get("deadline")),
            assignee=td.get("assignee", visit.brand.responsible),
        ))

    # 如果没有传入待办，生成默认 4 条
    if not payload.todos:
        default_todos = [
            {"priority": "P0", "title": "跟进联合投放方案确认",    "offset_days": 2},
            {"priority": "P0", "title": "跟进新品排期确认",        "offset_days": 5},
            {"priority": "P1", "title": "确认对方人员变动情况",     "offset_days": 10},
            {"priority": "P2", "title": "下次拜访准备",            "offset_days": 12},
        ]
        for td in default_todos:
            dl = (visit.visit_date + timedelta(days=td["offset_days"])) if visit.visit_date else None
            db.add(Todo(
                record_id=record.id,
                visit_id=payload.visit_id,
                priority=td["priority"],
                title=td["title"],
                deadline=dl,
                assignee=visit.brand.responsible if visit.brand else "采销",
            ))

    db.commit()
    db.refresh(record)

    return _format_record(record, visit)


@app.get("/api/records", response_model=List[RecordOut], tags=["拜访记录"])
def list_records(
    brand_id: Optional[int] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """近期拜访记录"""
    q = db.query(VisitRecord).join(Visit).order_by(desc(VisitRecord.created_at))
    if brand_id:
        q = q.filter(Visit.brand_id == brand_id)
    records = q.limit(limit).all()
    return [_format_record(r, r.visit) for r in records]


@app.get("/api/records/{record_id}", response_model=RecordOut, tags=["拜访记录"])
def get_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(VisitRecord).filter(VisitRecord.id == record_id).first()
    if not record:
        raise HTTPException(404, "记录不存在")
    return _format_record(record, record.visit)


# ================================================================
#  承诺
# ================================================================
@app.get("/api/commitments", response_model=List[CommitmentOut], tags=["承诺"])
def list_commitments(
    visit_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Commitment)
    if visit_id:
        q = q.filter(Commitment.visit_id == visit_id)
    if status:
        q = q.filter(Commitment.status == status)
    return q.order_by(desc(Commitment.created_at)).all()


@app.put("/api/commitments/{commitment_id}", response_model=CommitmentOut, tags=["承诺"])
def update_commitment(commitment_id: int, payload: CommitmentUpdate, db: Session = Depends(get_db)):
    c = db.query(Commitment).filter(Commitment.id == commitment_id).first()
    if not c:
        raise HTTPException(404, "承诺不存在")
    if payload.status:
        c.status = payload.status
        if payload.status == "fulfilled":
            c.fulfilled_at = datetime.now()
    if payload.deadline:
        c.deadline = payload.deadline
    db.commit()
    db.refresh(c)
    return c


# ================================================================
#  待办
# ================================================================
@app.get("/api/todos", response_model=List[TodoOut], tags=["待办"])
def list_todos(
    status: Optional[str] = Query(None, description="pending | done | overdue"),
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Todo)
    if status:
        q = q.filter(Todo.status == status)
    if priority:
        q = q.filter(Todo.priority == priority)
    if assignee:
        q = q.filter(Todo.assignee == assignee)
    return q.order_by(
        case((Todo.priority == "P0", 0), (Todo.priority == "P1", 1), else_=2),
        Todo.deadline.asc(),
    ).all()


@app.put("/api/todos/{todo_id}", response_model=TodoOut, tags=["待办"])
def update_todo(todo_id: int, payload: TodoUpdate, db: Session = Depends(get_db)):
    t = db.query(Todo).filter(Todo.id == todo_id).first()
    if not t:
        raise HTTPException(404, "待办不存在")
    if payload.status:
        t.status = payload.status
        if payload.status == "done":
            t.completed_at = datetime.now()
    if payload.priority:
        t.priority = payload.priority
    db.commit()
    db.refresh(t)
    return t


# ================================================================
#  拜访频率健康度
# ================================================================
@app.get("/api/health", response_model=List[HealthItem], tags=["健康度"])
def visit_health(db: Session = Depends(get_db)):
    """各品牌近 90 天拜访频率健康度"""
    brands = db.query(Brand).filter(Brand.status == "active").all()
    ninety_days_ago = date.today() - timedelta(days=90)

    result = []
    for brand in brands:
        count = db.query(func.count(Visit.id)).filter(
            Visit.brand_id == brand.id,
            Visit.status == "completed",
            Visit.visit_date >= ninety_days_ago,
        ).scalar() or 0

        # 健康度判断
        if brand.level == "S":
            healthy = count >= 3
            status_label = "达标" if healthy else ("偏低" if count >= 1 else "严重偏低")
        elif brand.level == "A":
            healthy = count >= 1
            status_label = "达标" if healthy else "偏低"
        else:
            healthy = count >= 1
            status_label = "达标" if healthy else "严重偏低"

        status_level = "green" if healthy else ("amber" if count > 0 else "red")

        result.append(HealthItem(
            brand_id=brand.id,
            brand_name=brand.name,
            name_key=brand.name_key,
            level=brand.level,
            baseline_freq=brand.baseline_freq or "季度/次",
            visit_count_90d=count,
            status_label=status_label,
            status_level=status_level,
        ))

    return result


# ================================================================
#  拜访前提醒
# ================================================================
@app.get("/api/brands/{name_key}/reminder", tags=["拜访提醒"])
def brand_visit_reminder(name_key: str, db: Session = Depends(get_db)):
    """获取品牌拜访前的提醒信息（档案 + 情报 + 承诺联动）"""
    brand = db.query(Brand).filter(Brand.name_key == name_key).first()
    if not brand:
        raise HTTPException(404, "品牌不存在")

    # 最近一次拜访
    last_visit = db.query(Visit).filter(
        Visit.brand_id == brand.id,
        Visit.status == "completed",
    ).order_by(desc(Visit.visit_date)).first()

    # 未兑现承诺
    pending_commitments = db.query(Commitment).filter(
        Commitment.visit.has(Visit.brand_id == brand.id),
        Commitment.status == "pending",
    ).all()

    # 超过 30 天未建联的联系人
    thirty_days_ago = date.today() - timedelta(days=30)
    stale_contacts = db.query(BrandContact).filter(
        BrandContact.brand_id == brand.id,
        BrandContact.last_contact_date < thirty_days_ago,
    ).all()

    return {
        "brand": brand.name,
        "level": brand.level,
        "relation_temp": brand.relation_temp,
        "archive_score": brand.archive_score,
        "last_visit_date": last_visit.visit_date if last_visit else None,
        "last_visit_purpose": last_visit.purpose if last_visit else None,
        "pending_commitments": [
            {"content": c.content, "deadline": c.deadline} for c in pending_commitments
        ],
        "stale_contacts": [
            {"name": c.name, "days_since": (date.today() - c.last_contact_date).days}
            for c in stale_contacts
        ],
        "days_since_last_visit": (
            (date.today() - last_visit.visit_date).days if last_visit else 999
        ),
    }


# ================================================================
#  辅助函数
# ================================================================
def _format_visit(visit: Visit, brand: Optional[Brand] = None) -> VisitOut:
    return VisitOut(
        id=visit.id,
        brand_id=visit.brand_id,
        brand_name=brand.name if brand else None,
        brand_level=brand.level if brand else None,
        visit_date=visit.visit_date,
        visit_time=visit.visit_time,
        visit_type=visit.visit_type,
        purpose=visit.purpose,
        notes=visit.notes,
        status=visit.status,
        record_id=visit.record_id,
        attendees=[
            VisitAttendeeOut(id=a.id, name=a.name, role=a.role, contact_id=a.contact_id)
            for a in (visit.attendees or [])
        ],
        created_at=visit.created_at,
        updated_at=visit.updated_at,
    )


def _format_record(record: VisitRecord, visit: Optional[Visit] = None) -> RecordOut:
    return RecordOut(
        id=record.id,
        visit_id=record.visit_id,
        participants=record.participants,
        topics=record.topics,
        commitments_raw=record.commitments_raw,
        undone_items=record.undone_items,
        relation_change=record.relation_change,
        next_visit_date=record.next_visit_date,
        visit_date=visit.visit_date if visit else None,
        brand_name=visit.brand.name if visit and visit.brand else None,
        brand_level=visit.brand.level if visit and visit.brand else None,
        visit_type=visit.visit_type if visit else None,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _parse_date(val) -> Optional[date]:
    if val is None:
        return None
    if isinstance(val, date):
        return val
    from datetime import datetime as dt
    try:
        return dt.strptime(str(val)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


# ---------- 入口 ----------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=SERVER_HOST, port=SERVER_PORT, reload=True)
