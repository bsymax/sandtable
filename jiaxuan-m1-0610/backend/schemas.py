"""
Pydantic 请求/响应模型
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Any

from pydantic import BaseModel, Field, field_serializer


class BrandBrief(BaseModel):
    id: int
    name: str
    name_key: str
    level: str
    responsible: Optional[str] = None
    archive_score: int = 0
    relation_temp: int = 50
    baseline_freq: Optional[str] = None

    class Config:
        from_attributes = True


class ContactOut(BaseModel):
    id: int
    brand_id: int
    name: str
    title: Optional[str] = None
    role_tag: Optional[str] = None
    phone: Optional[str] = None
    wechat: Optional[str] = None
    last_contact_date: Optional[date] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class BrandProfileOut(BaseModel):
    id: int
    brand_id: int
    founded_year: Optional[str] = None
    hq: Optional[str] = None
    positioning: Optional[str] = None
    org_structure: Optional[str] = None
    taboos: Optional[str] = None
    taboo_updated_by: Optional[str] = None
    taboo_updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BrandMetricsOut(BaseModel):
    id: int
    brand_id: int
    period_type: str
    period_value: str
    gmv: Optional[float] = None
    gmv_wow: Optional[float] = None
    gmv_yoy: Optional[float] = None
    orders: Optional[int] = None
    orders_wow: Optional[float] = None
    jd_share: Optional[float] = None
    jd_share_wow: Optional[float] = None
    tmall_share: Optional[float] = None
    douyin_share: Optional[float] = None
    pdd_share: Optional[float] = None
    channel_growth_jd: Optional[float] = None
    channel_growth_tmall: Optional[float] = None
    channel_growth_douyin: Optional[float] = None
    category_distribution: Optional[str] = None
    category_share: Optional[str] = None
    sku_count: Optional[int] = None
    p0_gap_count: Optional[int] = None
    gross_margin: Optional[float] = None
    uv_conversion: Optional[float] = None
    ad_rate: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_serializer(
        "gmv", "gmv_wow", "gmv_yoy", "orders_wow",
        "jd_share", "jd_share_wow", "tmall_share", "douyin_share", "pdd_share",
        "channel_growth_jd", "channel_growth_tmall", "channel_growth_douyin",
        "gross_margin", "uv_conversion", "ad_rate",
    )
    def serialize_decimal(self, v: Any) -> Optional[float]:
        if v is None:
            return None
        if isinstance(v, Decimal):
            return float(v)
        return float(v)

    class Config:
        from_attributes = True


class BrandProfileDetailOut(BaseModel):
    """GET /api/brands/profile/{name_key} 完整响应"""
    brand: BrandBrief
    profile: Optional[BrandProfileOut] = None
    contacts: List[ContactOut] = []
    metrics: Optional[BrandMetricsOut] = None
    completeness_score: int = 0
    completeness_max: int = 10
    completeness_percent: int = 0


class ContactPatch(BaseModel):
    id: int
    name: Optional[str] = None
    title: Optional[str] = None
    role_tag: Optional[str] = None
    phone: Optional[str] = None
    wechat: Optional[str] = None


class BrandProfileUpdate(BaseModel):
    taboos: Optional[str] = None
    contacts: Optional[List[ContactPatch]] = None
