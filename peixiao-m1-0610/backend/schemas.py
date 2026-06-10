"""
Pydantic 请求/响应模型
"""

from datetime import date, time, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


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
# 通用响应
# ==============================
class ApiResponse(BaseModel):
    success: bool = True
    message: str = "ok"
    data: Optional[dict] = None
