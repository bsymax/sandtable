"""
品牌档案模块路由（佳璇，2026-06-11 合并进主工程）
- GET  /api/brands/profile/{name_key}   品牌档案（含完整度评分）
- GET  /api/brands/metrics/{name_key}   近 N 月经营指标
- PUT  /api/brands/profile/{name_key}   更新潜规则 / 竞争格局 / 增长机会 / 关键联系人

注意：本路由必须先于 routers/brands.py 注册（main.py 中 include 顺序），
否则 /api/brands/profile/{x} 会被 /api/brands/{name_key} 抢先匹配。
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from database import get_db, engine
from config import DW_METRICS_PERIOD_TYPE
from deps_auth import AuthUser, get_current_user_optional, require_name_key, require_writable
from llm_prompts import (
    blurb_fallback,
    build_strategy_llm_context,
    is_strategy_field_empty,
    parse_strategy_json,
    resolve_strategy_baseline,
)
from llm_service import complete
from models import Brand, BrandContact, BrandProfile, BrandMetrics, IntelAlert
from completeness import calc_completeness, count_brand_intel, count_brand_interactions
from org_structure import apply_org_update, dump_org_structure, parse_org_structure, sync_org_from_contacts
from schemas import (
    BrandProfileDetailOut, BrandOut, BrandProfileOut, ContactOut, BrandMetricsOut,
    BrandProfileUpdate, AiStrategyOut, AiBlurbOut, OrgImageOut, normalize_role_tag,
)

router = APIRouter()

UPLOAD_ROOT = Path(__file__).resolve().parent.parent / "uploads"
ORG_UPLOAD_ROOT = UPLOAD_ROOT / "org"
ORG_UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
ALLOWED_ORG_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_ORG_IMAGE_BYTES = 5 * 1024 * 1024


def _remove_org_image_file(image_url: str | None) -> None:
    if not image_url or not image_url.startswith("/uploads/org/"):
        return
    rel = image_url[len("/uploads/org/"):]
    path = ORG_UPLOAD_ROOT / rel
    if path.is_file():
        try:
            path.unlink()
        except OSError:
            pass


def _build_profile_response(brand, profile, contacts, metrics, db: Session):
    intel_count = count_brand_intel(db, engine, brand.id)
    interaction_count = count_brand_interactions(db, engine, brand.id)
    comp = calc_completeness(
        profile,
        contacts,
        metrics,
        intel_count=intel_count,
        interaction_count=interaction_count,
    )
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
    """品牌档案：基础信息 + 简介 + 联系人 + 最新一月经营指标 + 完整度评分"""
    require_name_key(user, name_key)
    brand = db.query(Brand).filter(Brand.name_key == name_key).first()
    if not brand:
        raise HTTPException(status_code=404, detail=f"品牌不存在: {name_key}")

    profile = db.query(BrandProfile).filter(BrandProfile.brand_id == brand.id).first()
    metrics = (
        db.query(BrandMetrics)
        .filter(BrandMetrics.brand_id == brand.id, BrandMetrics.period_type == DW_METRICS_PERIOD_TYPE)
        .order_by(BrandMetrics.period_value.desc())
        .first()
    )
    contacts = [c for c in brand.contacts if c.is_active]
    return _build_profile_response(brand, profile, contacts, metrics, db)


@router.get("/api/brands/metrics/{name_key}", response_model=List[BrandMetricsOut], tags=["品牌档案"])
def list_brand_metrics(
    name_key: str,
    limit: int = Query(12, ge=1, le=52),
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """返回最近 N 条月度经营指标（按 period_value 倒序）"""
    require_name_key(user, name_key)
    brand = db.query(Brand).filter(Brand.name_key == name_key).first()
    if not brand:
        raise HTTPException(status_code=404, detail=f"品牌不存在: {name_key}")

    rows = (
        db.query(BrandMetrics)
        .filter(BrandMetrics.brand_id == brand.id, BrandMetrics.period_type == DW_METRICS_PERIOD_TYPE)
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
    require_writable(user)
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
        profile.competitive_landscape = (
            None if is_strategy_field_empty(payload.competitive_landscape) else payload.competitive_landscape
        )

    if payload.growth_opportunities is not None:
        profile.growth_opportunities = (
            None if is_strategy_field_empty(payload.growth_opportunities) else payload.growth_opportunities
        )

    if payload.founded_year is not None:
        profile.founded_year = payload.founded_year.strip() or None
    if payload.hq is not None:
        profile.hq = payload.hq.strip() or None
    if payload.positioning is not None:
        profile.positioning = payload.positioning.strip() or None
    if payload.responsible is not None:
        brand.responsible = payload.responsible.strip() or None

    if payload.org is not None:
        apply_org_update(profile, payload.org.model_dump(exclude_unset=True))
        db.flush()

    contacts_changed = False

    if payload.contacts_remove:
        for cid in payload.contacts_remove:
            contact = (
                db.query(BrandContact)
                .filter(BrandContact.id == cid, BrandContact.brand_id == brand.id)
                .first()
            )
            if contact:
                contact.is_active = False
                contacts_changed = True

    if payload.contacts_add:
        for item in payload.contacts_add:
            name = (item.name or "").strip()
            if not name:
                continue
            db.add(
                BrandContact(
                    brand_id=brand.id,
                    name=name,
                    title=item.title,
                    role_tag=normalize_role_tag(item.role_tag),
                    phone=item.phone,
                    wechat=item.wechat,
                    is_active=True,
                )
            )
            contacts_changed = True
        db.flush()

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
                contact.role_tag = normalize_role_tag(item.role_tag)
            if item.phone is not None:
                contact.phone = item.phone
            if item.wechat is not None:
                contact.wechat = item.wechat
            contacts_changed = True

    db.commit()
    db.refresh(profile)
    brand = db.query(Brand).filter(Brand.id == brand.id).first()
    contacts = (
        db.query(BrandContact)
        .filter(BrandContact.brand_id == brand.id, BrandContact.is_active == True)
        .all()
    )
    if contacts_changed:
        sync_org_from_contacts(profile, contacts)
        db.commit()
        db.refresh(profile)
    metrics = (
        db.query(BrandMetrics)
        .filter(BrandMetrics.brand_id == brand.id, BrandMetrics.period_type == DW_METRICS_PERIOD_TYPE)
        .order_by(BrandMetrics.period_value.desc())
        .first()
    )
    return _build_profile_response(brand, profile, contacts, metrics, db)


@router.post("/api/brands/profile/{name_key}/ai/strategy", response_model=AiStrategyOut, tags=["品牌档案"])
async def ai_strategy(
    name_key: str,
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """Tab2 竞争与机会 · LLM ON 时生成；失败降级档案内文案"""
    require_name_key(user, name_key)
    brand = db.query(Brand).filter(Brand.name_key == name_key).first()
    if not brand:
        raise HTTPException(status_code=404, detail=f"品牌不存在: {name_key}")
    profile = db.query(BrandProfile).filter(BrandProfile.brand_id == brand.id).first()
    metrics = (
        db.query(BrandMetrics)
        .filter(BrandMetrics.brand_id == brand.id, BrandMetrics.period_type == DW_METRICS_PERIOD_TYPE)
        .order_by(BrandMetrics.period_value.desc())
        .first()
    )
    alerts = (
        db.query(IntelAlert)
        .filter(
            IntelAlert.brand_id == brand.id,
            IntelAlert.status != "closed",
            IntelAlert.priority.in_(["P0", "P1"]),
        )
        .order_by(IntelAlert.created_at.desc())
        .limit(10)
        .all()
    )
    fb_landscape, fb_opportunities = resolve_strategy_baseline(
        profile.competitive_landscape if profile else None,
        profile.growth_opportunities if profile else None,
        brand,
        profile,
        metrics,
        alerts,
    )
    ctx = build_strategy_llm_context(brand, profile, metrics, fb_landscape, fb_opportunities)

    raw = await complete(
        "你是京东采销的品牌竞争分析助手。根据经营数据与情报撰写简洁中文分析。"
        "禁止输出「暂无」「请在 Tab2 手工维护」等占位语；必须给出可执行要点。",
        ctx,
        max_tokens=600,
        db=db,
        auth_user=user,
        route="profile.ai.strategy",
    )
    parsed = parse_strategy_json(raw) if raw else None
    if parsed:
        return AiStrategyOut(
            source="llm",
            name_key=name_key,
            competitive_landscape=parsed.get("competitive_landscape") or fb_landscape,
            growth_opportunities=parsed.get("growth_opportunities") or fb_opportunities,
        )
    return AiStrategyOut(
        source="fallback",
        name_key=name_key,
        competitive_landscape=fb_landscape,
        growth_opportunities=fb_opportunities,
        message="LLM 未启用或调用失败，已返回档案内现有文案",
    )


@router.post("/api/brands/profile/{name_key}/ai/blurb", response_model=AiBlurbOut, tags=["品牌档案"])
async def ai_blurb(
    name_key: str,
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """Tab1 规则段 · LLM ON 时一段话解读"""
    require_name_key(user, name_key)
    brand = db.query(Brand).filter(Brand.name_key == name_key).first()
    if not brand:
        raise HTTPException(status_code=404, detail=f"品牌不存在: {name_key}")
    metrics = (
        db.query(BrandMetrics)
        .filter(BrandMetrics.brand_id == brand.id, BrandMetrics.period_type == DW_METRICS_PERIOD_TYPE)
        .order_by(BrandMetrics.period_value.desc())
        .first()
    )
    alert_n = db.query(IntelAlert).filter(
        IntelAlert.brand_id == brand.id,
        IntelAlert.priority.in_(["P0", "P1"]),
        IntelAlert.status != "closed",
    ).count()
    fallback = blurb_fallback(brand.name, metrics, alert_n)
    text = await complete(
        "你是品牌经营解读助手，一段话概括风险与机会，简体中文，可含少量 HTML strong 标签。"
        "经营指标为月频：使用「月成交（万元）」与「成交同比」，勿写「周 GMV」。",
        fallback.replace("（规则版解读 · LLM 未启用）", ""),
        max_tokens=300,
        db=db,
        auth_user=user,
        route="profile.ai.blurb",
    )
    if text:
        return AiBlurbOut(source="llm", name_key=name_key, summary=text.strip())
    return AiBlurbOut(source="fallback", name_key=name_key, summary=fallback)


@router.post("/api/brands/profile/{name_key}/org-image", response_model=OrgImageOut, tags=["品牌档案"])
async def upload_org_image(
    name_key: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """上传品牌组织架构图（JPEG/PNG/WebP/GIF · 最大 5MB）"""
    require_writable(user)
    require_name_key(user, name_key)
    brand = db.query(Brand).filter(Brand.name_key == name_key).first()
    if not brand:
        raise HTTPException(status_code=404, detail=f"品牌不存在: {name_key}")
    profile = db.query(BrandProfile).filter(BrandProfile.brand_id == brand.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="品牌简介尚未初始化")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_ORG_IMAGE_EXT:
        raise HTTPException(status_code=400, detail="仅支持 JPG/PNG/WebP/GIF 图片")

    content = await file.read()
    if len(content) > MAX_ORG_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="图片不能超过 5MB")
    if not content:
        raise HTTPException(status_code=400, detail="文件为空")

    brand_dir = ORG_UPLOAD_ROOT / name_key
    brand_dir.mkdir(parents=True, exist_ok=True)
    filename = f"org-{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
    dest = brand_dir / filename
    dest.write_bytes(content)

    org = parse_org_structure(profile.org_structure)
    _remove_org_image_file(org.get("image_url"))
    image_url = f"/uploads/org/{name_key}/{filename}"
    org["image_url"] = image_url
    org["image_updated_at"] = datetime.now().strftime("%Y-%m-%d")
    profile.org_structure = dump_org_structure(org)
    db.commit()
    db.refresh(profile)

    return OrgImageOut(
        image_url=image_url,
        image_updated_at=org["image_updated_at"],
        org_structure=profile.org_structure,
    )


@router.delete("/api/brands/profile/{name_key}/org-image", response_model=BrandProfileDetailOut, tags=["品牌档案"])
def delete_org_image(
    name_key: str,
    db: Session = Depends(get_db),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
):
    """删除已上传的组织架构图"""
    require_writable(user)
    require_name_key(user, name_key)
    brand = db.query(Brand).filter(Brand.name_key == name_key).first()
    if not brand:
        raise HTTPException(status_code=404, detail=f"品牌不存在: {name_key}")
    profile = db.query(BrandProfile).filter(BrandProfile.brand_id == brand.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="品牌简介尚未初始化")

    org = parse_org_structure(profile.org_structure)
    _remove_org_image_file(org.get("image_url"))
    org.pop("image_url", None)
    org.pop("image_updated_at", None)
    profile.org_structure = dump_org_structure(org)
    db.commit()
    db.refresh(profile)

    contacts = (
        db.query(BrandContact)
        .filter(BrandContact.brand_id == brand.id, BrandContact.is_active == True)
        .all()
    )
    metrics = (
        db.query(BrandMetrics)
        .filter(BrandMetrics.brand_id == brand.id, BrandMetrics.period_type == DW_METRICS_PERIOD_TYPE)
        .order_by(BrandMetrics.period_value.desc())
        .first()
    )
    return _build_profile_response(brand, profile, contacts, metrics, db)
