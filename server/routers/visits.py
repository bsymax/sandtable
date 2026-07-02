"""
拜访模块路由
来源：peixiao-m1-0610/backend/main.py，2026-06-10 由 Max 拆分入主工程（逻辑零改动）。
归属：培翛。涵盖 拜访安排 / 拜访记录 / 承诺 / 待办 / 频率健康度。
M6: 新增 POST /api/visits/import-history 历史拜访批量导入
"""

import re
import csv
import io
from datetime import date, time, datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, case

from database import get_db
from deps_auth import (
    AuthUser,
    filter_by_brand_ids,
    filter_brand_query,
    get_current_user_optional,
    require_brand_id,
    require_writable,
)
from models import Brand, Visit, VisitAttendee, VisitRecord, Commitment, Todo
from schemas import (
    VisitCreate, VisitOut, VisitUpdate, VisitAttendeeOut,
    RecordCreate, RecordOut,
    CommitmentOut, CommitmentUpdate,
    TodoOut, TodoUpdate,
    HealthItem, ApiResponse, AiExtractOut,
    VisitImportResult,
)
from llm_service import complete

router = APIRouter()


# ================================================================
#  拜访安排
# ================================================================
@router.post("/api/visits", response_model=VisitOut, tags=["拜访"])
def create_visit(
    payload: VisitCreate,
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """安排新拜访"""
    require_writable(user)
    require_brand_id(user, payload.brand_id)
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
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """拜访列表（支持筛选）"""
    q = db.query(Visit)

    if status:
        q = q.filter(Visit.status == status)
    if brand_id:
        require_brand_id(user, brand_id)
        q = q.filter(Visit.brand_id == brand_id)
    else:
        q = filter_by_brand_ids(q, Visit.brand_id, user)
    if month:
        q = q.filter(func.date_format(Visit.visit_date, "%Y-%m") == month)

    q = q.order_by(desc(Visit.visit_date))
    return [_format_visit(v, v.brand) for v in q.all()]


@router.get("/api/visits/{visit_id}", response_model=VisitOut, tags=["拜访"])
def get_visit(
    visit_id: int,
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(404, "拜访不存在")
    require_brand_id(user, visit.brand_id)
    return _format_visit(visit, visit.brand)


@router.put("/api/visits/{visit_id}", response_model=VisitOut, tags=["拜访"])
def update_visit(
    visit_id: int,
    payload: VisitUpdate,
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """更新拜访状态 / 时间"""
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(404, "拜访不存在")
    require_writable(user)
    require_brand_id(user, visit.brand_id)

    update_data = payload.dict(exclude_unset=True)
    for k, v in update_data.items():
        setattr(visit, k, v)
    db.commit()
    db.refresh(visit)
    return _format_visit(visit, visit.brand)


@router.delete("/api/visits/{visit_id}", response_model=ApiResponse, tags=["拜访"])
def delete_visit(
    visit_id: int,
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(404, "拜访不存在")
    require_writable(user)
    require_brand_id(user, visit.brand_id)
    db.delete(visit)
    db.commit()
    return ApiResponse(message="拜访已删除")


# ================================================================
#  拜访记录
# ================================================================
@router.post("/api/records", response_model=RecordOut, tags=["拜访记录"])
def create_record(
    payload: RecordCreate,
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """保存拜访后记录，自动生成待办"""
    visit = db.query(Visit).filter(Visit.id == payload.visit_id).first()
    if not visit:
        raise HTTPException(404, "拜访不存在")
    require_writable(user)
    require_brand_id(user, visit.brand_id)

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

    if payload.ai_commitments:
        for ac in payload.ai_commitments:
            content = (ac.get("content") or "").strip()
            if not content:
                continue
            db.add(Commitment(
                visit_id=payload.visit_id,
                record_id=record.id,
                content=content[:255],
                party=ac.get("party") or "brand",
                status="pending",
                deadline=_parse_date(ac.get("deadline")),
            ))
    else:
        for c in _parse_commitment_lines(payload.commitments_raw, payload.visit_id, record.id):
            db.add(c)

    if payload.todos:
        for td in payload.todos:
            db.add(Todo(
                record_id=record.id,
                visit_id=payload.visit_id,
                priority=td.get("priority", "P2"),
                title=td.get("title", ""),
                deadline=_parse_date(td.get("deadline")),
                assignee=td.get("assignee", visit.brand.responsible),
            ))
    elif payload.todos is None:
        # 兼容旧前端：未传 todos 时仍生成默认待办
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
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """近期拜访记录"""
    q = db.query(VisitRecord).join(Visit).order_by(desc(VisitRecord.created_at))
    if brand_id:
        require_brand_id(user, brand_id)
        q = q.filter(Visit.brand_id == brand_id)
    else:
        q = filter_by_brand_ids(q, Visit.brand_id, user)
    records = q.limit(limit).all()
    return [_format_record(r, r.visit) for r in records]


@router.get("/api/records/{record_id}", response_model=RecordOut, tags=["拜访记录"])
def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    record = db.query(VisitRecord).filter(VisitRecord.id == record_id).first()
    if not record:
        raise HTTPException(404, "记录不存在")
    if record.visit:
        require_brand_id(user, record.visit.brand_id)
    return _format_record(record, record.visit)


@router.post("/api/records/{record_id}/ai/extract", response_model=AiExtractOut, tags=["拜访记录"])
async def ai_extract_record(
    record_id: int,
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """纪要 → 待办/承诺抽取（M3-B；LLM 失败降级规则解析，须前端人工确认后落库）"""
    record = db.query(VisitRecord).filter(VisitRecord.id == record_id).first()
    if not record:
        raise HTTPException(404, "记录不存在")
    visit = record.visit
    if visit:
        require_brand_id(user, visit.brand_id)

    rule_todos = []
    rule_commits = []
    if record.commitments_raw:
        for line in record.commitments_raw.splitlines():
            line = line.strip().lstrip("-•·").strip()
            if len(line) >= 2:
                rule_commits.append({"content": line, "party": "brand", "title": line})

    ctx = f"拜访纪要：\n{record.topics or ''}\n承诺原文：\n{record.commitments_raw or ''}\n"
    ctx += '输出 JSON：{"todos":[{"title":"","priority":"P1|P2"}],"commitments":[{"title":"","priority":"P1"}]}'
    raw = await complete(
        "从拜访纪要抽取待办与承诺，简体中文，仅输出 JSON",
        ctx,
        max_tokens=500,
        db=db,
        auth_user=user,
        route="visits.ai.extract",
    )
    if raw:
        try:
            import json
            import re
            text = raw.strip()
            m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
            if m:
                text = m.group(1)
            data = json.loads(text)
            return AiExtractOut(
                source="llm",
                record_id=record_id,
                todos=data.get("todos") or rule_todos,
                commitments=data.get("commitments") or rule_commits,
            )
        except Exception:
            pass
    return AiExtractOut(
        source="fallback",
        record_id=record_id,
        todos=rule_todos,
        commitments=rule_commits,
        message="LLM 未启用或解析失败，已返回规则切行结果，请人工确认",
    )


# ================================================================
#  承诺
# ================================================================
@router.get("/api/commitments", response_model=List[CommitmentOut], tags=["承诺"])
def list_commitments(
    visit_id: Optional[int] = None,
    status: Optional[str] = None,
    brand_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    q = db.query(Commitment)
    joined_visit = False
    if visit_id:
        q = q.filter(Commitment.visit_id == visit_id)
    if status:
        q = q.filter(Commitment.status == status)
    if brand_id or (user and not user.is_admin):
        q = q.join(Visit, Commitment.visit_id == Visit.id)
        joined_visit = True
    if brand_id:
        require_brand_id(user, brand_id)
        q = q.filter(Visit.brand_id == brand_id)
    elif user and not user.is_admin:
        q = filter_by_brand_ids(q, Visit.brand_id, user)
    if visit_id and user and not joined_visit:
        visit = db.query(Visit).filter(Visit.id == visit_id).first()
        if visit:
            require_brand_id(user, visit.brand_id)
    return q.order_by(desc(Commitment.created_at)).all()


@router.put("/api/commitments/{commitment_id}", response_model=CommitmentOut, tags=["承诺"])
def update_commitment(
    commitment_id: int,
    payload: CommitmentUpdate,
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    c = db.query(Commitment).filter(Commitment.id == commitment_id).first()
    if not c:
        raise HTTPException(404, "承诺不存在")
    require_writable(user)
    visit = db.query(Visit).filter(Visit.id == c.visit_id).first()
    if visit:
        require_brand_id(user, visit.brand_id)

    data = payload.model_dump(exclude_unset=True)
    if "content" in data:
        text = (data["content"] or "").strip()
        if not text:
            raise HTTPException(400, "承诺内容不能为空")
        if len(text) > 255:
            raise HTTPException(400, "承诺内容不能超过 255 字")
        c.content = text
    if "party" in data:
        party = (data["party"] or "").strip().lower()
        if party not in ("brand", "bd"):
            raise HTTPException(400, "承诺方须为 brand 或 bd")
        c.party = party
    if "deadline" in data:
        c.deadline = data["deadline"]
    if "status" in data and data["status"]:
        status = data["status"]
        if status not in ("pending", "fulfilled", "broken"):
            raise HTTPException(400, "status 须为 pending / fulfilled / broken")
        c.status = status
        if status == "fulfilled":
            c.fulfilled_at = datetime.now()
        elif status in ("pending", "broken"):
            c.fulfilled_at = None

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
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    q = db.query(Todo).options(joinedload(Todo.visit).joinedload(Visit.brand)).join(Visit)
    q = filter_by_brand_ids(q, Visit.brand_id, user)
    if status:
        q = q.filter(Todo.status == status)
    if priority:
        q = q.filter(Todo.priority == priority)
    if assignee:
        q = q.filter(Todo.assignee == assignee)
    rows = q.order_by(
        case((Todo.priority == "P0", 0), (Todo.priority == "P1", 1), else_=2),
        Todo.deadline.asc(),
    ).all()
    return [_format_todo(t) for t in rows]


@router.put("/api/todos/{todo_id}", response_model=TodoOut, tags=["待办"])
def update_todo(
    todo_id: int,
    payload: TodoUpdate,
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    t = db.query(Todo).options(
        joinedload(Todo.visit).joinedload(Visit.brand)
    ).filter(Todo.id == todo_id).first()
    if not t:
        raise HTTPException(404, "待办不存在")
    require_writable(user)
    if t.visit:
        require_brand_id(user, t.visit.brand_id)
    if payload.status:
        t.status = payload.status
        if payload.status == "done":
            t.completed_at = datetime.now()
    if payload.priority:
        t.priority = payload.priority
    db.commit()
    db.refresh(t)
    return _format_todo(t)


# ================================================================
#  拜访频率健康度
# ================================================================
@router.get("/api/health", response_model=List[HealthItem], tags=["健康度"])
def visit_health(
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """各品牌近 90 天拜访频率健康度"""
    q = db.query(Brand).filter(Brand.status == "active")
    brands = filter_brand_query(q, user).all()
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
#  M6 历史拜访批量导入
# ================================================================
@router.post("/api/visits/import-history", response_model=VisitImportResult, tags=["拜访"])
async def import_history_visits(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """上传 CSV/Excel 批量导入已完成的历史拜访 + 记录"""
    require_writable(user)

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = content.decode("gbk")
        except Exception:
            raise HTTPException(400, "文件编码不支持，请保存为 UTF-8")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(400, "CSV 表头为空")

    # 跳过中文表头/填写说明行：以 brand_key 开头的行为英文字段名行（培翛 M6-0701-3）
    text_lines = text.splitlines()
    header_idx = None
    for i, line in enumerate(text_lines):
        first_cell = (line.split(",")[0] if line else "").strip().lower()
        if first_cell == "brand_key":
            header_idx = i
            break
    if header_idx is None:
        raise HTTPException(400, "CSV 未找到 brand_key 表头行，请使用模板下载的格式")

    reader2 = csv.DictReader(io.StringIO("\n".join(text_lines[header_idx:])))
    if not reader2.fieldnames:
        raise HTTPException(400, "CSV 表头为空")
    norm = {h.strip().lower().replace(" ", "_"): h for h in reader2.fieldnames}

    def get_col(row, *names):
        for n in names:
            if n in norm and norm[n] in row:
                v = (row[norm[n]] or "").strip()
                if v:
                    return v
        return ""

    brand_cache = {b.name_key: b for b in db.query(Brand).filter(Brand.status == "active").all()}
    brand_cache.update({b.name: b for b in brand_cache.values()})

    created = 0
    updated = 0
    failed = 0
    errors = []

    for idx, row in enumerate(reader2, start=header_idx + 2):
        try:
            brand_key_val = get_col(row, "brand_key")
            # 跳过说明行、空行、占位行
            if not brand_key_val or brand_key_val.startswith("【") or brand_key_val.upper() == "YYYY-MM-DD":
                continue
            brand = brand_cache.get(brand_key_val) or brand_cache.get(brand_key_val.lower())
            if not brand:
                failed += 1
                errors.append({"row": idx, "reason": f"品牌 '{brand_key_val}' 未找到"})
                continue
            # 跳过用户无权限的品牌行（不中断整个导入）
            if user and not user.is_admin:
                allowed = getattr(user, 'brand_ids', None)
                if allowed is not None and brand.id not in (allowed or []):
                    failed += 1
                    errors.append({"row": idx, "reason": f"无品牌 '{brand_key_val}' 权限"})
                    continue

            visit_date_str = get_col(row, "visit_date")
            if not visit_date_str:
                failed += 1
                errors.append({"row": idx, "reason": "缺少 visit_date"})
                continue
            visit_date_val = _parse_date(visit_date_str)
            if not visit_date_val:
                failed += 1
                errors.append({"row": idx, "reason": f"日期格式错误: {visit_date_str}"})
                continue

            purpose = get_col(row, "purpose")
            visit_type_val = get_col(row, "visit_type") or "regular"
            if visit_type_val not in ("urgent", "regular", "renewal"):
                visit_type_val = "regular"

            # 判重：brand_id + visit_date + purpose(前50字)
            purpose_key = (purpose or "")[:50]
            existing = db.query(Visit).filter(
                Visit.brand_id == brand.id,
                Visit.visit_date == visit_date_val,
                func.left(Visit.purpose, 50) == purpose_key,
            ).first()

            if existing:
                # 更新已有拜访和记录
                existing.visit_type = visit_type_val
                existing.purpose = purpose or existing.purpose
                existing.status = "completed"
                existing.notes = get_col(row, "participants") or existing.notes
                record = db.query(VisitRecord).filter(
                    VisitRecord.visit_id == existing.id
                ).first()
                if not record:
                    record = VisitRecord(visit_id=existing.id)
                    db.add(record)
                    db.flush()
                record.topics = get_col(row, "topics") or record.topics
                record.commitments_raw = get_col(row, "commitments_raw") or record.commitments_raw
                record.undone_items = get_col(row, "undone_items") or record.undone_items
                rc = get_col(row, "relation_change")
                if rc in ("up", "flat", "down"):
                    record.relation_change = rc
                nvd = get_col(row, "next_visit_date")
                if nvd:
                    record.next_visit_date = _parse_date(nvd)
                updated += 1
            else:
                visit = Visit(
                    brand_id=brand.id,
                    visit_date=visit_date_val,
                    visit_time=time(14, 0),
                    visit_type=visit_type_val,
                    purpose=purpose or "(历史导入)",
                    notes=get_col(row, "participants") or None,
                    status="completed",
                )
                db.add(visit)
                db.flush()
                record = VisitRecord(
                    visit_id=visit.id,
                    topics=get_col(row, "topics") or None,
                    commitments_raw=get_col(row, "commitments_raw") or None,
                    undone_items=get_col(row, "undone_items") or None,
                    relation_change=(get_col(row, "relation_change") or "flat"),
                    next_visit_date=_parse_date(get_col(row, "next_visit_date")),
                )
                db.add(record)
                db.flush()
                visit.record_id = record.id

                # 从 commitments_raw 按行拆条写入承诺
                if record.commitments_raw:
                    for c_item in _parse_commitment_lines(
                        record.commitments_raw, visit.id, record.id
                    ):
                        db.add(c_item)

                created += 1

        except Exception as e:
            failed += 1
            errors.append({"row": idx, "reason": str(e)})

    db.commit()

    return VisitImportResult(
        created=created,
        updated=updated,
        failed=failed,
        errors=errors,
    )


# ================================================================
#  辅助函数
# ================================================================
def _format_todo(t: Todo) -> TodoOut:
    brand = t.visit.brand if t.visit else None
    return TodoOut(
        id=t.id,
        record_id=t.record_id,
        visit_id=t.visit_id,
        brand_name=brand.name if brand else None,
        brand_key=brand.name_key if brand else None,
        priority=t.priority,
        title=t.title,
        deadline=t.deadline,
        assignee=t.assignee,
        status=t.status,
        created_at=t.created_at,
        completed_at=t.completed_at,
    )


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
