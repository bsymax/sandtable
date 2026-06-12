"""
拜访模块路由
来源：peixiao-m1-0610/backend/main.py，2026-06-10 由 Max 拆分入主工程（逻辑零改动）。
归属：培翛。涵盖 拜访安排 / 拜访记录 / 承诺 / 待办 / 频率健康度。
"""

import re
from datetime import date, time, datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, case

from database import get_db
from models import Brand, Visit, VisitAttendee, VisitRecord, Commitment, Todo
from schemas import (
    VisitCreate, VisitOut, VisitUpdate, VisitAttendeeOut,
    RecordCreate, RecordOut,
    CommitmentOut, CommitmentUpdate,
    TodoOut, TodoUpdate,
    HealthItem, ApiResponse,
)

router = APIRouter()


# ================================================================
#  拜访安排
# ================================================================
@router.post("/api/visits", response_model=VisitOut, tags=["拜访"])
def create_visit(payload: VisitCreate, db: Session = Depends(get_db)):
    """安排新拜访"""
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
    db.flush()

    for name in payload.attendee_names:
        if name.strip():
            db.add(VisitAttendee(visit_id=visit.id, name=name.strip(), role="brand"))

    db.commit()
    db.refresh(visit)

    return _format_visit(visit, brand)


@router.get("/api/visits", response_model=List[VisitOut], tags=["拜访"])
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
    return [_format_visit(v, v.brand) for v in q.all()]


@router.get("/api/visits/{visit_id}", response_model=VisitOut, tags=["拜访"])
def get_visit(visit_id: int, db: Session = Depends(get_db)):
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(404, "拜访不存在")
    return _format_visit(visit, visit.brand)


@router.put("/api/visits/{visit_id}", response_model=VisitOut, tags=["拜访"])
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


@router.delete("/api/visits/{visit_id}", response_model=ApiResponse, tags=["拜访"])
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
@router.post("/api/records", response_model=RecordOut, tags=["拜访记录"])
def create_record(payload: RecordCreate, db: Session = Depends(get_db)):
    """保存拜访后记录，自动生成待办"""
    visit = db.query(Visit).filter(Visit.id == payload.visit_id).first()
    if not visit:
        raise HTTPException(404, "拜访不存在")

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

    visit.status = "completed"
    visit.record_id = record.id

    for c in _parse_commitment_lines(payload.commitments_raw, payload.visit_id, record.id):
        db.add(c)

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


@router.get("/api/records", response_model=List[RecordOut], tags=["拜访记录"])
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


@router.get("/api/records/{record_id}", response_model=RecordOut, tags=["拜访记录"])
def get_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(VisitRecord).filter(VisitRecord.id == record_id).first()
    if not record:
        raise HTTPException(404, "记录不存在")
    return _format_record(record, record.visit)


# ================================================================
#  承诺
# ================================================================
@router.get("/api/commitments", response_model=List[CommitmentOut], tags=["承诺"])
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


@router.put("/api/commitments/{commitment_id}", response_model=CommitmentOut, tags=["承诺"])
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
@router.get("/api/todos", response_model=List[TodoOut], tags=["待办"])
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


@router.put("/api/todos/{todo_id}", response_model=TodoOut, tags=["待办"])
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
@router.get("/api/health", response_model=List[HealthItem], tags=["健康度"])
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


def _parse_commitment_lines(raw: Optional[str], visit_id: int, record_id: int) -> List[Commitment]:
    """按行解析 commitments_raw，每行 - 开头写入 commitments 表（S2）。"""
    if not raw:
        return []
    party = "brand"
    result: List[Commitment] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if "品牌方" in stripped and "承诺" in stripped:
            party = "brand"
            continue
        if ("我方" in stripped or "BD" in stripped) and "承诺" in stripped:
            party = "bd"
            continue
        if not stripped.startswith("-"):
            continue
        content = re.sub(r"^-\s*", "", stripped)
        content = re.sub(r"^【[^】]+】\s*", "", content).strip()[:255]
        if content:
            result.append(Commitment(
                visit_id=visit_id,
                record_id=record_id,
                content=content,
                party=party,
                status="pending",
            ))
    return result
