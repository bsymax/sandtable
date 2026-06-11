"""
Pydantic 请求/响应模型 · 情报模块
"""
from datetime import date, time, datetime
from typing import Optional, List
from pydantic import BaseModel


# --- 品牌（下拉用）---
class BrandBrief(BaseModel):
    id: int
    name: str
    name_key: str
    level: str
    class Config: from_attributes = True


# --- 新闻 ---
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


# --- 周报 ---
class IntelWeeklyReportOut(BaseModel):
    id: int
    brand_id: int
    brand_name: Optional[str] = None
    week_start: date
    week_end: date
    week_label: Optional[str] = None
    weekly_gmv: Optional[int] = None
    gmv_change: Optional[int] = None
    competitor_moves: Optional[str] = None
    inventory_status: Optional[str] = None
    risk_points: Optional[str] = None
    opportunities: Optional[str] = None
    next_week_plan: Optional[str] = None
    reporter: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    class Config: from_attributes = True

class IntelWeeklyReportCreate(BaseModel):
    brand_id: int
    week_start: date
    week_end: date
    week_label: Optional[str] = None
    weekly_gmv: Optional[int] = None
    gmv_change: Optional[int] = None
    competitor_moves: Optional[str] = None
    inventory_status: Optional[str] = None
    risk_points: Optional[str] = None
    opportunities: Optional[str] = None
    next_week_plan: Optional[str] = None
    reporter: Optional[str] = None


# --- 预警 ---
class IntelAlertOut(BaseModel):
    id: int
    brand_id: Optional[int] = None
    brand_name: Optional[str] = None
    brand_level: Optional[str] = None
    news_id: Optional[int] = None
    weekly_id: Optional[int] = None
    visit_id: Optional[int] = None
    priority: str
    title: str
    description: Optional[str] = None
    suggestion: Optional[str] = None
    ai_confidence: Optional[int] = None
    status: str
    assignee: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    class Config: from_attributes = True

class IntelAlertCreate(BaseModel):
    brand_id: Optional[int] = None
    news_id: Optional[int] = None
    priority: str = "P2"
    title: str
    description: Optional[str] = None
    suggestion: Optional[str] = None
    assignee: Optional[str] = None

class IntelAlertUpdate(BaseModel):
    priority: Optional[str] = None
    status: Optional[str] = None
    assignee: Optional[str] = None
    suggestion: Optional[str] = None


# --- 简报 ---
class IntelBriefingOut(BaseModel):
    brand_id: int
    brand_name: str
    brand_level: str
    recent_news: List[IntelNewsOut] = []
    active_alerts: List[IntelAlertOut] = []
    latest_weekly: Optional[dict] = None
    stats: dict = {}


# --- 统计 ---
class IntelStatsOut(BaseModel):
    total_news_week: int = 0
    total_alerts: int = 0
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0


# --- 通用 ---
class ApiResponse(BaseModel):
    success: bool = True
    message: str = "ok"
    data: Optional[dict] = None
