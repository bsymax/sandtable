"""
品牌模块路由（基底版）
来源：peixiao-m1-0610/backend/main.py 中的品牌/联系人/提醒接口，2026-06-10 由 Max 拆分入主工程。
归属：公共基底（brands / brand_contacts 表），业务 owner = 佳璇（S1 起在此扩展档案接口）。
约定：佳璇新增的品牌档案接口放 /api/brands/profile/...，不改动本文件已有接口的路径与返回结构。
"""

from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, noload
from sqlalchemy import desc, case, or_

from database import get_db
from deps_auth import filter_brand_query, get_current_user_optional, require_name_key, AuthUser
from models import Brand, BrandContact, Visit, Commitment, IntelAlert, BrandMetrics
from schemas import BrandOut, BrandBrief, ContactOut

router = APIRouter()


def _brand_base_query(db: Session):
    """列表/详情只读 brands 表字段，避免 selectin 拉取 profile/metrics 触发旧库缺列 500"""
    return db.query(Brand).options(
        noload(Brand.contacts),
        noload(Brand.visits),
        noload(Brand.profile),
        noload(Brand.metrics),
    )

@router.get("/api/brands", response_model=List[BrandBrief], tags=["品牌"])
def list_brands(
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """品牌下拉列表（按等级排序）；登录后仅返回负责品牌"""
    q = _brand_base_query(db).filter(Brand.status == "active")
    q = filter_brand_query(q, user)
    return q.order_by(
        case(
            (Brand.level == "S", 0),
            (Brand.level == "A", 1),
            (Brand.level == "B", 2),
            else_=3,
        )
    ).all()


@router.get("/api/brands/detail", response_model=List[BrandOut], tags=["品牌"])
def list_brands_detail(
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """品牌列表（含完整度、温度等）"""
    q = _brand_base_query(db).filter(Brand.status == "active")
    q = filter_brand_query(q, user)
    return q.order_by(Brand.id).all()


@router.get("/api/brands/{name_key}", response_model=BrandOut, tags=["品牌"])
def get_brand(
    name_key: str,
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """按 name_key 获取品牌详情"""
    require_name_key(user, name_key)
    brand = _brand_base_query(db).filter(Brand.name_key == name_key, Brand.status == "active").first()
    if not brand:
        raise HTTPException(404, "品牌不存在")
    return brand


@router.get("/api/brands/{brand_id}/contacts", response_model=List[ContactOut], tags=["联系人"])
def list_contacts(brand_id: int, db: Session = Depends(get_db)):
    return db.query(BrandContact).filter(
        BrandContact.brand_id == brand_id,
        BrandContact.is_active == True,
    ).all()


@router.get("/api/brands/{name_key}/reminder", tags=["拜访提醒"])
def brand_visit_reminder(
    name_key: str,
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """获取品牌拜访前的提醒信息（档案 + 情报 + 承诺联动）"""
    require_name_key(user, name_key)
    brand = _brand_base_query(db).filter(Brand.name_key == name_key).first()
    if not brand:
        raise HTTPException(404, "品牌不存在")

    last_visit = db.query(Visit).filter(
        Visit.brand_id == brand.id,
        Visit.status == "completed",
    ).order_by(desc(Visit.visit_date)).first()

    pending_commitments = db.query(Commitment).filter(
        Commitment.visit.has(Visit.brand_id == brand.id),
        Commitment.status == "pending",
    ).all()

    broken_commitments = db.query(Commitment).filter(
        Commitment.visit.has(Visit.brand_id == brand.id),
        Commitment.status == "broken",
    ).all()

    thirty_days_ago = date.today() - timedelta(days=30)
    stale_contacts = db.query(BrandContact).filter(
        BrandContact.brand_id == brand.id,
        BrandContact.last_contact_date < thirty_days_ago,
    ).all()

    p0_alerts = db.query(IntelAlert).filter(
        IntelAlert.brand_id == brand.id,
        IntelAlert.priority == "P0",
        IntelAlert.status.in_(["pending", "confirmed"]),
    ).order_by(
        case((IntelAlert.category == "风险预警", 0), else_=1),
        desc(IntelAlert.created_at),
    ).limit(5).all()

    latest_weekly = db.query(BrandMetrics).filter(
        BrandMetrics.brand_id == brand.id,
        BrandMetrics.period_type == "weekly",
        or_(
            BrandMetrics.intel_report_status.isnot(None),
            BrandMetrics.risk_points.isnot(None),
            BrandMetrics.opportunities.isnot(None),
        ),
    ).order_by(desc(BrandMetrics.week_start), desc(BrandMetrics.id)).first()

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
        "broken_commitments": [
            {"content": c.content, "deadline": c.deadline} for c in broken_commitments
        ],
        "stale_contacts": [
            {"name": c.name, "days_since": (date.today() - c.last_contact_date).days}
            for c in stale_contacts
        ],
        "p0_alerts": [
            {
                "title": a.title,
                "category": a.category,
                "priority": a.priority,
                "description": a.description,
                "suggestion": a.suggestion,
            }
            for a in p0_alerts
        ],
        "latest_weekly": {
            "week_label": latest_weekly.period_value if latest_weekly else None,
            "competitor_moves": latest_weekly.competitor_moves if latest_weekly else None,
            "risk_points": latest_weekly.risk_points if latest_weekly else None,
            "opportunities": latest_weekly.opportunities if latest_weekly else None,
        } if latest_weekly else None,
        "days_since_last_visit": (
            (date.today() - last_visit.visit_date).days if last_visit else 999
        ),
    }
