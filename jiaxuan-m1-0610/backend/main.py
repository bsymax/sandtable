"""
FastAPI 主应用 —— 品牌档案模块 API
启动命令: python3 main.py
端口: 8001
"""

from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from config import SERVER_HOST, SERVER_PORT
from database import get_db, engine
from models import Base, Brand, BrandContact, BrandProfile, BrandMetrics
from completeness import calc_completeness
from schemas import (
    BrandProfileDetailOut, BrandBrief, BrandProfileOut, ContactOut, BrandMetricsOut,
    BrandProfileUpdate,
)

Base.metadata.create_all(bind=engine)

from seed import run_seed
run_seed()

app = FastAPI(
    title="品牌沙盘 M1 · 品牌档案 API",
    version="1.0.0",
    description="品牌简介与经营看板数据 API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/brands/profile/{name_key}", response_model=BrandProfileDetailOut, tags=["品牌档案"])
def get_brand_profile(name_key: str, db: Session = Depends(get_db)):
    """
    根据 name_key 获取品牌档案：
    - 品牌基础信息
    - 品牌简介（brand_profiles）
    - 关键联系人（brand_contacts，培翛公共表）
    - 最新一周经营指标（brand_metrics）
    """
    brand = db.query(Brand).filter(Brand.name_key == name_key).first()
    if not brand:
        raise HTTPException(status_code=404, detail=f"品牌不存在: {name_key}")

    profile = (
        db.query(BrandProfile)
        .filter(BrandProfile.brand_id == brand.id)
        .first()
    )

    metrics = (
        db.query(BrandMetrics)
        .filter(
            BrandMetrics.brand_id == brand.id,
            BrandMetrics.period_type == "weekly",
        )
        .order_by(BrandMetrics.period_value.desc())
        .first()
    )

    contacts = [c for c in brand.contacts if c.is_active]

    return _build_profile_response(brand, profile, contacts, metrics)


def _build_profile_response(brand, profile, contacts, metrics):
    comp = calc_completeness(profile, contacts, metrics)
    return BrandProfileDetailOut(
        brand=BrandBrief.model_validate(brand),
        profile=BrandProfileOut.model_validate(profile) if profile else None,
        contacts=[ContactOut.model_validate(c) for c in contacts],
        metrics=BrandMetricsOut.model_validate(metrics) if metrics else None,
        **comp,
    )


@app.get("/api/brands/metrics/{name_key}", response_model=List[BrandMetricsOut], tags=["品牌档案"])
def list_brand_metrics(
    name_key: str,
    limit: int = Query(12, ge=1, le=52),
    db: Session = Depends(get_db),
):
    """返回最近 N 条周度经营指标（按 period_value 倒序）"""
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


@app.put("/api/brands/profile/{name_key}", response_model=BrandProfileDetailOut, tags=["品牌档案"])
def update_brand_profile(name_key: str, payload: BrandProfileUpdate, db: Session = Depends(get_db)):
    """更新品牌档案：潜规则 + 关键联系人"""
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


@app.get("/health", tags=["系统"])
def health_check():
    return {"status": "ok", "module": "brand-profile"}


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
FRONTEND_HTML = FRONTEND_DIR / "brand_profile_api.html"


@app.get("/", include_in_schema=False)
def serve_frontend():
    """浏览器直接打开 http://127.0.0.1:8001/ 即可访问品牌档案页"""
    if not FRONTEND_HTML.is_file():
        raise HTTPException(status_code=404, detail="frontend/brand_profile_api.html 不存在")
    return FileResponse(FRONTEND_HTML, media_type="text/html; charset=utf-8")


if FRONTEND_DIR.is_dir():
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=SERVER_HOST, port=SERVER_PORT, reload=True)
