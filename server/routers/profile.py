"""
品牌档案模块路由（佳璇，2026-06-11 合并进主工程）
- GET  /api/brands/profile/{name_key}   品牌档案（含完整度评分）
- GET  /api/brands/metrics/{name_key}   近 N 周经营指标
- PUT  /api/brands/profile/{name_key}   更新潜规则 / 竞争格局 / 增长机会 / 关键联系人

注意：本路由必须先于 routers/brands.py 注册（main.py 中 include 顺序），
否则 /api/brands/profile/{x} 会被 /api/brands/{name_key} 抢先匹配。
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from deps_auth import AuthUser, get_current_user_optional, require_name_key
from models import Brand, BrandContact, BrandProfile, BrandMetrics
from completeness import calc_completeness
from schemas import (
    BrandProfileDetailOut, BrandOut, BrandProfileOut, ContactOut, BrandMetricsOut,
    BrandProfileUpdate,
)

router = APIRouter()


def _build_profile_response(brand, profile, contacts, metrics):
    comp = calc_completeness(profile, contacts, metrics)
    return BrandProfileDetailOut(
        brand=BrandOut.model_validate(brand),
        profile=BrandProfileOut.model_validate(profile) if profile else None,
        contacts=[ContactOut.model_validate(c) for c in contacts],
        metrics=BrandMetricsOut.model_validate(metrics) if metrics else None,
        **comp,
    )


@router.get("/api/brands/profile/{name_key}", response_model=BrandProfileDetailOut, tags=["品牌档案"])
def get_brand_profile(
    name_key: str,
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """品牌档案：基础信息 + 简介 + 联系人 + 最新一周经营指标 + 完整度评分"""
    require_name_key(user, name_key)
    brand = db.query(Brand).filter(Brand.name_key == name_key).first()
    if not brand:
        raise HTTPException(status_code=404, detail=f"品牌不存在: {name_key}")

    profile = db.query(BrandProfile).filter(BrandProfile.brand_id == brand.id).first()
    metrics = (
        db.query(BrandMetrics)
        .filter(BrandMetrics.brand_id == brand.id, BrandMetrics.period_type == "weekly")
        .order_by(BrandMetrics.period_value.desc())
        .first()
    )
    contacts = [c for c in brand.contacts if c.is_active]
    return _build_profile_response(brand, profile, contacts, metrics)


@router.get("/api/brands/metrics/{name_key}", response_model=List[BrandMetricsOut], tags=["品牌档案"])
def list_brand_metrics(
    name_key: str,
    limit: int = Query(12, ge=1, le=52),
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """返回最近 N 条周度经营指标（按 period_value 倒序）"""
    require_name_key(user, name_key)
    brand = db.query(Brand).filter(Brand.name_key == name_key).first()
    if not brand:
        raise HTTPException(status_code=404, detail=f"品牌不存在: {name_key}")

    rows = (
        db.query(BrandMetrics)
        .filter(BrandMetrics.brand_id == brand.id, BrandMetrics.period_type == "weekly")
        .order_by(BrandMetrics.period_value.desc())
        .limit(limit)
        .all()
    )
    return [BrandMetricsOut.model_validate(r) for r in rows]


@router.put("/api/brands/profile/{name_key}", response_model=BrandProfileDetailOut, tags=["品牌档案"])
def update_brand_profile(
    name_key: str,
    payload: BrandProfileUpdate,
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """更新品牌档案：潜规则 + 竞争/机会 + 关键联系人"""
    require_name_key(user, name_key)
    brand = db.query(Brand).filter(Brand.name_key == name_key).first()
    if not brand:
        raise HTTPException(status_code=404, detail=f"品牌不存在: {name_key}")

    profile = db.query(BrandProfile).filter(BrandProfile.brand_id == brand.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="品牌简介尚未初始化")

    if payload.taboos is not None:
        profile.taboos = payload.taboos
        profile.taboo_updated_by = brand.responsible or "采销"
        profile.taboo_updated_at = datetime.now()

    if payload.competitive_landscape is not None:
        profile.competitive_landscape = payload.competitive_landscape

    if payload.growth_opportunities is not None:
        profile.growth_opportunities = payload.growth_opportunities

    if payload.contacts:
        for item in payload.contacts:
            contact = (
                db.query(BrandContact)
                .filter(BrandContact.id == item.id, BrandContact.brand_id == brand.id)
                .first()
            )
            if not contact:
                raise HTTPException(status_code=404, detail=f"联系人不存在: {item.id}")
            if item.name is not None:
                contact.name = item.name
            if item.title is not None:
                contact.title = item.title
            if item.role_tag is not None:
                contact.role_tag = item.role_tag
            if item.phone is not None:
                contact.phone = item.phone
            if item.wechat is not None:
                contact.wechat = item.wechat

    db.commit()
    db.refresh(profile)
    brand = db.query(Brand).filter(Brand.id == brand.id).first()
    contacts = (
        db.query(BrandContact)
        .filter(BrandContact.brand_id == brand.id, BrandContact.is_active == True)
        .all()
    )
    metrics = (
        db.query(BrandMetrics)
        .filter(BrandMetrics.brand_id == brand.id, BrandMetrics.period_type == "weekly")
        .order_by(BrandMetrics.period_value.desc())
        .first()
    )
    return _build_profile_response(brand, profile, contacts, metrics)


@router.post("/api/brands/profile/{name_key}/ai/strategy", tags=["品牌档案"])
async def ai_strategy(
    name_key: str,
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """Tab2 竞争与机会 · LLM 骨架（M3-B 联调；当前返回 fallback）"""
    require_name_key(user, name_key)
    brand = db.query(Brand).filter(Brand.name_key == name_key).first()
    if not brand:
        raise HTTPException(status_code=404, detail=f"品牌不存在: {name_key}")
    profile = db.query(BrandProfile).filter(BrandProfile.brand_id == brand.id).first()
    landscape = profile.competitive_landscape if profile else None
    opportunities = profile.growth_opportunities if profile else None
    return {
        "source": "fallback",
        "name_key": name_key,
        "competitive_landscape": landscape or "暂无竞争格局描述，请在 Tab2 手工维护。",
        "growth_opportunities": opportunities or "暂无增长机会描述，请在 Tab2 手工维护。",
        "message": "LLM 未启用或联调中，已返回档案内现有文案",
    }
