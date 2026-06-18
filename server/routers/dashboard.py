"""M3 工作台聚合 · 规则一行 + LLM 槽位"""

from datetime import date, timedelta

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from deps_auth import AuthUser, filter_brand_query, filter_by_brand_ids, get_current_user_optional
from llm_prompts import dashboard_summary_fallback
from llm_service import complete
from models import Brand, Todo, Visit, Commitment, IntelAlert
from schemas import DashboardSummaryOut

router = APIRouter()


def _rule_summary(db: Session, user: Optional[AuthUser]) -> str:
    todo_q = db.query(Todo).join(Visit)
    todo_q = filter_by_brand_ids(todo_q, Visit.brand_id, user)
    todos = todo_q.filter(Todo.status != "done").all()
    today = date.today()
    overdue = sum(1 for t in todos if t.deadline and t.deadline < today)

    cq = db.query(Commitment).join(Visit, Commitment.visit_id == Visit.id)
    cq = filter_by_brand_ids(cq, Visit.brand_id, user)
    commit_pending = cq.filter(Commitment.status == "pending").count()

    aq = db.query(IntelAlert).filter(
        IntelAlert.priority.in_(["P0", "P1"]),
        IntelAlert.status != "closed",
    )
    aq = filter_by_brand_ids(aq, IntelAlert.brand_id, user)
    p0p1 = aq.count()

    brands = filter_brand_query(db.query(Brand).filter(Brand.status == "active"), user).all()
    ninety = date.today() - timedelta(days=90)
    health_warn = 0
    for b in brands:
        cnt = db.query(func.count(Visit.id)).filter(
            Visit.brand_id == b.id,
            Visit.status == "completed",
            Visit.visit_date >= ninety,
        ).scalar() or 0
        need = 3 if b.level == "S" else 1
        if cnt < need:
            health_warn += 1

    return dashboard_summary_fallback(
        len(todos), overdue, commit_pending, p0p1, health_warn
    )


@router.get("/api/dashboard/summary-line", response_model=DashboardSummaryOut, tags=["工作台"])
async def dashboard_summary_line(
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """工作台 #dashboard-summary-line · LLM OFF 时返回规则版"""
    fallback = _rule_summary(db, user)
    text = await complete(
        "你是厨小事业部品牌沙盘助手，用一两句话概括采销今日最该优先处理的事项，简体中文，不超过 120 字。",
        fallback.replace("（规则版 · LLM 未启用）", ""),
        max_tokens=200,
        db=db,
        auth_user=user,
        route="dashboard.summary_line",
    )
    if text:
        return DashboardSummaryOut(source="llm", summary=text.strip())
    return DashboardSummaryOut(source="fallback", summary=fallback)
