"""
Pydantic 请求/响应模型
"""

from datetime import date, time, datetime
from decimal import Decimal
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_serializer


# ==============================
# 品牌
# ==============================
class BrandOut(BaseModel):
    id: int
    name: str
    name_key: str
    level: str
    responsible: Optional[str] = None
    archive_score: int
    relation_temp: int
    baseline_freq: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config: from_attributes = True


class BrandBrief(BaseModel):
    """下拉列表用"""
    id: int
    name: str
    name_key: str
    level: str

    class Config: from_attributes = True


# ==============================
# 联系人
# ==============================
class ContactOut(BaseModel):
    id: int
    brand_id: int
    name: str
    title: Optional[str] = None
    role_tag: Optional[str] = None
    phone: Optional[str] = None
    wechat: Optional[str] = None
    last_contact_date: Optional[date] = None
    is_active: bool

    class Config: from_attributes = True


# ==============================
# 拜访安排
# ==============================
class VisitCreate(BaseModel):
    brand_id: int
    visit_date: date
    visit_time: Optional[time] = time(14, 0)
    visit_type: str = "regular"          # urgent | regular | renewal
    purpose: str
    notes: Optional[str] = None
    attendee_names: List[str] = []       # 参与人员姓名列表


class VisitAttendeeOut(BaseModel):
    id: int
    name: str
    role: str
    contact_id: Optional[int] = None

    class Config: from_attributes = True


class VisitOut(BaseModel):
    id: int
    brand_id: int
    brand_name: Optional[str] = None
    brand_level: Optional[str] = None
    visit_date: date
    visit_time: Optional[time] = None
    visit_type: str
    purpose: str
    notes: Optional[str] = None
    status: str
    record_id: Optional[int] = None
    attendees: List[VisitAttendeeOut] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config: from_attributes = True


class VisitUpdate(BaseModel):
    visit_date: Optional[date] = None
    visit_time: Optional[time] = None
    visit_type: Optional[str] = None
    purpose: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None          # scheduled | completed | cancelled


# ==============================
# 拜访记录
# ==============================
class RecordCreate(BaseModel):
    visit_id: int
    participants: Optional[str] = None
    topics: Optional[str] = None
    commitments_raw: Optional[str] = None  # 原始承诺文本
    undone_items: Optional[str] = None
    relation_change: str = "flat"
    next_visit_date: Optional[date] = None
    # AI 待办抽取
    todos: List[dict] = []                # [{priority, title, deadline, assignee}]


class RecordOut(BaseModel):
    id: int
    visit_id: int
    participants: Optional[str] = None
    topics: Optional[str] = None
    commitments_raw: Optional[str] = None
    undone_items: Optional[str] = None
    relation_change: Optional[str] = None
    next_visit_date: Optional[date] = None
    visit_date: Optional[date] = None
    brand_name: Optional[str] = None
    brand_level: Optional[str] = None
    visit_type: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config: from_attributes = True


# ==============================
# 承诺
# ==============================
class CommitmentOut(BaseModel):
    id: int
    visit_id: int
    record_id: Optional[int] = None
    content: str
    party: str
    status: str
    deadline: Optional[date] = None
    fulfilled_at: Optional[datetime] = None

    class Config: from_attributes = True


class CommitmentUpdate(BaseModel):
    status: Optional[str] = None           # pending | fulfilled | broken
    deadline: Optional[date] = None


# ==============================
# 待办
# ==============================
class TodoOut(BaseModel):
    id: int
    record_id: Optional[int] = None
    visit_id: Optional[int] = None
    brand_name: Optional[str] = None
    brand_key: Optional[str] = None
    priority: str
    title: str
    deadline: Optional[date] = None
    assignee: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config: from_attributes = True


class TodoUpdate(BaseModel):
    status: Optional[str] = None           # pending | done | overdue
    priority: Optional[str] = None


# ==============================
# 健康度
# ==============================
class HealthItem(BaseModel):
    brand_id: int
    brand_name: str
    name_key: str
    level: str
    baseline_freq: str
    visit_count_90d: int = 0
    status_label: str = "达标"              # 达标 | 偏低 | 严重偏低
    status_level: str = "green"            # green | amber | red


# ==============================
# 品牌档案（佳璇，2026-06-11 合并）
# ==============================
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

    class Config: from_attributes = True


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
        return float(v)

    class Config: from_attributes = True


class BrandProfileDetailOut(BaseModel):
    """GET /api/brands/profile/{name_key} 完整响应"""
    brand: BrandOut
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


# ==============================
# 情报模块（开开，2026-06-11 合并）
# ==============================
class IntelNewsOut(BaseModel):
    id: int
    brand_id: Optional[int] = None
    brand_name: Optional[str] = None
    title: str
    summary: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    sentiment: Optional[str] = None
    category: Optional[str] = None
    keywords: Optional[str] = None
    published_at: Optional[datetime] = None
    fetched_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config: from_attributes = True


class IntelNewsCreate(BaseModel):
    brand_id: Optional[int] = None
    title: str
    summary: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    sentiment: Optional[str] = "neutral"
    category: Optional[str] = None
    keywords: Optional[str] = None
    published_at: Optional[datetime] = None


class IntelNewsUpdate(BaseModel):
    brand_id: Optional[int] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    sentiment: Optional[str] = None
    category: Optional[str] = None
    keywords: Optional[str] = None
    published_at: Optional[datetime] = None


class IntelWeeklyReportOut(BaseModel):
    id: int
    brand_id: int
    brand_name: Optional[str] = None
    week_start: date
    week_end: date
    week_label: Optional[str] = None
    weekly_gmv: Optional[float] = None
    gmv_change: Optional[float] = None
    competitor_moves: Optional[str] = None
    inventory_status: Optional[str] = None
    risk_points: Optional[str] = None
    opportunities: Optional[str] = None
    next_week_plan: Optional[str] = None
    reporter: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_serializer("weekly_gmv", "gmv_change")
    def serialize_decimal(self, v: Any) -> Optional[float]:
        if v is None:
            return None
        return float(v)

    class Config: from_attributes = True


class IntelWeeklyReportCreate(BaseModel):
    brand_id: int
    week_start: date
    week_end: date
    week_label: Optional[str] = None
    weekly_gmv: Optional[float] = None
    gmv_change: Optional[float] = None
    competitor_moves: Optional[str] = None
    inventory_status: Optional[str] = None
    risk_points: Optional[str] = None
    opportunities: Optional[str] = None
    next_week_plan: Optional[str] = None
    reporter: Optional[str] = None


class IntelWeeklyReportUpdate(BaseModel):
    week_start: Optional[date] = None
    week_end: Optional[date] = None
    week_label: Optional[str] = None
    weekly_gmv: Optional[float] = None
    gmv_change: Optional[float] = None
    competitor_moves: Optional[str] = None
    inventory_status: Optional[str] = None
    risk_points: Optional[str] = None
    opportunities: Optional[str] = None
    next_week_plan: Optional[str] = None
    reporter: Optional[str] = None
    status: Optional[str] = None


class IntelAlertOut(BaseModel):
    id: int
    brand_id: Optional[int] = None
    brand_name: Optional[str] = None
    brand_name_key: Optional[str] = None
    brand_level: Optional[str] = None
    news_id: Optional[int] = None
    weekly_id: Optional[int] = None
    visit_id: Optional[int] = None
    priority: str
    category: Optional[str] = None
    title: str
    description: Optional[str] = None
    suggestion: Optional[str] = None
    ai_confidence: Optional[float] = None
    status: str
    assignee: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_serializer("ai_confidence")
    def serialize_decimal(self, v: Any) -> Optional[float]:
        if v is None:
            return None
        return float(v)

    class Config: from_attributes = True


class IntelAlertCreate(BaseModel):
    brand_id: Optional[int] = None
    news_id: Optional[int] = None
    priority: str = "P2"
    category: Optional[str] = None
    title: str
    description: Optional[str] = None
    suggestion: Optional[str] = None
    assignee: Optional[str] = None


class IntelAlertUpdate(BaseModel):
    priority: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    assignee: Optional[str] = None
    suggestion: Optional[str] = None


class IntelBriefingOut(BaseModel):
    brand_id: int
    brand_name: str
    brand_level: str
    recent_news: List[IntelNewsOut] = []
    active_alerts: List[IntelAlertOut] = []
    latest_weekly: Optional[dict] = None
    stats: dict = {}


class IntelStatsOut(BaseModel):
    total_news_week: int = 0
    total_alerts: int = 0
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0


# ==============================
# 通用响应
# ==============================
class ApiResponse(BaseModel):
    success: bool = True
    message: str = "ok"
    data: Optional[dict] = None
