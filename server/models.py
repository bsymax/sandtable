"""
SQLAlchemy ORM 模型定义
对应 schema.sql 中的 7 张表
"""

from datetime import date, time, datetime
from typing import Optional, List

from sqlalchemy import (
    Column, Integer, String, Text, Date, Time, DateTime, Enum,
    ForeignKey, Boolean, Numeric, JSON, func,
)
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# ---------- 品牌 ----------
class Brand(Base):
    __tablename__ = "brands"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    name          = Column(String(64), nullable=False, comment="品牌名称")
    name_key      = Column(String(32), nullable=False, unique=True, comment="品牌英文标识")
    level         = Column(Enum("S", "A", "B", "C"), nullable=False, default="B")
    responsible   = Column(String(32))
    archive_score = Column(Integer, default=0, comment="档案完整度 0-100")
    relation_temp = Column(Integer, default=50, comment="关系温度 0-100")
    baseline_freq = Column(String(32), default="季度/次")
    status        = Column(Enum("active", "inactive"), nullable=False, default="active")
    created_at    = Column(DateTime, server_default=func.now())
    updated_at    = Column(DateTime, server_default=func.now(), onupdate=func.now())

    contacts = relationship("BrandContact", back_populates="brand", lazy="selectin")
    visits   = relationship("Visit",       back_populates="brand", lazy="selectin")
    profile  = relationship("BrandProfile", back_populates="brand", uselist=False, lazy="selectin")
    metrics  = relationship("BrandMetrics", back_populates="brand", lazy="selectin")


# ---------- 品牌联系人 ----------
class BrandContact(Base):
    __tablename__ = "brand_contacts"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    brand_id         = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    name             = Column(String(32), nullable=False)
    title            = Column(String(64))
    role_tag         = Column(String(32), default="日常对接")
    phone            = Column(String(20))
    wechat           = Column(String(32))
    last_contact_date = Column(Date)
    is_active        = Column(Boolean, default=True)
    created_at       = Column(DateTime, server_default=func.now())
    updated_at       = Column(DateTime, server_default=func.now(), onupdate=func.now())

    brand = relationship("Brand", back_populates="contacts")


# ---------- 拜访安排 ----------
class Visit(Base):
    __tablename__ = "visits"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    brand_id   = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    visit_date = Column(Date, nullable=False)
    visit_time = Column(Time, default=time(14, 0))
    visit_type = Column(Enum("urgent", "regular", "renewal"), nullable=False, default="regular")
    purpose    = Column(Text, nullable=False)
    notes      = Column(Text)
    status     = Column(Enum("scheduled", "completed", "cancelled"), nullable=False, default="scheduled")
    record_id  = Column(Integer, nullable=True, comment="关联拜访记录ID（非外键，冗余字段）")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    brand      = relationship("Brand", back_populates="visits")
    attendees  = relationship("VisitAttendee", back_populates="visit", lazy="selectin")
    record     = relationship("VisitRecord",
                              primaryjoin="foreign(Visit.id) == VisitRecord.visit_id",
                              uselist=False, viewonly=True, sync_backref=False)
    commitments = relationship("Commitment", back_populates="visit", lazy="selectin")
    todos      = relationship("Todo", back_populates="visit", lazy="selectin")


# ---------- 拜访参与人员 ----------
class VisitAttendee(Base):
    __tablename__ = "visit_attendees"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    visit_id   = Column(Integer, ForeignKey("visits.id", ondelete="CASCADE"), nullable=False)
    contact_id = Column(Integer, ForeignKey("brand_contacts.id", ondelete="SET NULL"), nullable=True)
    name       = Column(String(32), nullable=False)
    role       = Column(Enum("bd", "brand"), default="bd", comment="bd=采销方, brand=品牌方")
    created_at = Column(DateTime, server_default=func.now())

    visit   = relationship("Visit", back_populates="attendees")
    contact = relationship("BrandContact")


# ---------- 拜访后记录 ----------
class VisitRecord(Base):
    __tablename__ = "visit_records"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    visit_id        = Column(Integer, ForeignKey("visits.id", ondelete="CASCADE"), unique=True, nullable=False)
    participants    = Column(Text)
    topics          = Column(Text)
    commitments_raw = Column(Text)
    undone_items    = Column(Text)
    relation_change = Column(Enum("up", "flat", "down"), default="flat")
    next_visit_date = Column(Date)
    created_at      = Column(DateTime, server_default=func.now())
    updated_at      = Column(DateTime, server_default=func.now(), onupdate=func.now())

    visit       = relationship("Visit", foreign_keys=[visit_id])
    commit       = relationship("Commitment", back_populates="record", lazy="selectin")
    todos        = relationship("Todo", back_populates="record", lazy="selectin")


# ---------- 承诺事项 ----------
class Commitment(Base):
    __tablename__ = "commitments"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    visit_id     = Column(Integer, ForeignKey("visits.id", ondelete="CASCADE"), nullable=False)
    record_id    = Column(Integer, ForeignKey("visit_records.id", ondelete="SET NULL"))
    content      = Column(String(255), nullable=False)
    party        = Column(Enum("brand", "bd"), default="brand")
    status       = Column(Enum("pending", "fulfilled", "broken"), nullable=False, default="pending")
    deadline     = Column(Date)
    fulfilled_at = Column(DateTime)
    created_at   = Column(DateTime, server_default=func.now())
    updated_at   = Column(DateTime, server_default=func.now(), onupdate=func.now())

    visit  = relationship("Visit", back_populates="commitments")
    record = relationship("VisitRecord", back_populates="commit")


# ---------- 待办事项 ----------
class Todo(Base):
    __tablename__ = "todos"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    record_id    = Column(Integer, ForeignKey("visit_records.id", ondelete="SET NULL"))
    visit_id     = Column(Integer, ForeignKey("visits.id", ondelete="SET NULL"))
    priority     = Column(Enum("P0", "P1", "P2", "P3"), nullable=False, default="P2")
    title        = Column(String(255), nullable=False)
    deadline     = Column(Date)
    assignee     = Column(String(32))
    status       = Column(Enum("pending", "done", "overdue"), nullable=False, default="pending")
    created_at   = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)

    visit  = relationship("Visit", back_populates="todos")
    record = relationship("VisitRecord", back_populates="todos")


# ================================================================
# 品牌档案模块（佳璇，2026-06-11 合并）
# ================================================================

# ---------- 品牌档案简介 ----------
class BrandProfile(Base):
    __tablename__ = "brand_profiles"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    brand_id         = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    founded_year     = Column(String(16))
    hq               = Column(String(64))
    positioning      = Column(String(255))
    org_structure    = Column(Text, comment="组织架构（JSON文本）")
    taboos                  = Column(Text, comment="品牌潜规则")
    competitive_landscape   = Column(Text, comment="竞争格局（M2 可编辑）")
    growth_opportunities    = Column(Text, comment="增长机会（M2 可编辑）")
    taboo_updated_by        = Column(String(32))
    taboo_updated_at        = Column(DateTime)
    created_at              = Column(DateTime, server_default=func.now())
    updated_at       = Column(DateTime, server_default=func.now(), onupdate=func.now())

    brand = relationship("Brand", back_populates="profile")


# ---------- 品牌经营指标快照 ----------
class BrandMetrics(Base):
    __tablename__ = "brand_metrics"

    id                    = Column(Integer, primary_key=True, autoincrement=True)
    brand_id              = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    period_type           = Column(Enum("weekly", "monthly"), nullable=False, default="weekly")
    period_value          = Column(String(16), nullable=False, comment="周期标识，如 2026W23")
    gmv                   = Column(Numeric(12, 2))
    gmv_wow               = Column(Numeric(6, 2))
    gmv_yoy               = Column(Numeric(6, 2))
    sales_volume          = Column(Integer, comment="销量")
    sales_volume_wow      = Column(Numeric(6, 2), comment="销量环比%")
    sales_volume_yoy      = Column(Numeric(6, 2), comment="销量同比%")
    jd_share              = Column(Numeric(5, 2))
    jd_share_wow          = Column(Numeric(5, 2))
    tmall_share           = Column(Numeric(5, 2))
    douyin_share          = Column(Numeric(5, 2))
    pdd_share             = Column(Numeric(5, 2))
    taobao_share          = Column(Numeric(5, 2), comment="淘宝市占%")
    channel_growth_jd     = Column(Numeric(8, 2))
    channel_growth_tmall  = Column(Numeric(8, 2))
    channel_growth_douyin = Column(Numeric(8, 2))
    channel_growth_taobao = Column(Numeric(8, 2), comment="淘宝渠道增速%")
    category_distribution = Column(Text, comment="三级类目GMV占比 JSON")
    category_share        = Column(Text, comment="各类目JD市占 JSON")
    sku_count             = Column(Integer)
    p0_gap_count          = Column(Integer)
    gross_margin          = Column(Numeric(5, 2))
    uv_conversion         = Column(Numeric(5, 2))
    ad_rate               = Column(Numeric(5, 2))
    # 情报周报叙事字段（与档案 brand_metrics 共用，GMV 以 gmv/gmv_wow 为准）
    week_start            = Column(Date, comment="周开始日期")
    week_end              = Column(Date, comment="周结束日期")
    competitor_moves      = Column(Text, comment="竞品动态")
    inventory_status      = Column(Text, comment="库存状况")
    risk_points           = Column(Text, comment="风险点")
    opportunities         = Column(Text, comment="机会点")
    next_week_plan        = Column(Text, comment="下周计划")
    reporter              = Column(String(32), comment="填报人")
    intel_report_status   = Column(Enum("draft", "submitted"), comment="情报周报状态")
    created_at            = Column(DateTime, server_default=func.now())
    updated_at            = Column(DateTime, server_default=func.now(), onupdate=func.now())

    brand = relationship("Brand", back_populates="metrics")


# ================================================================
# 情报模块（开开，2026-06-11 合并）
# ================================================================

# ---------- 外部新闻/资讯 ----------
class IntelNews(Base):
    __tablename__ = "intel_news"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    brand_id      = Column(Integer, ForeignKey("brands.id", ondelete="SET NULL"), nullable=True)
    title         = Column(String(255), nullable=False)
    summary       = Column(Text)
    url           = Column(String(512))
    source        = Column(String(64))
    sentiment     = Column(Enum("positive", "negative", "neutral"), default="neutral")
    category      = Column(String(32))
    keywords      = Column(String(255))
    url_fingerprint = Column(String(64), comment="URL SHA256去重指纹")
    published_at  = Column(DateTime)
    fetched_at    = Column(DateTime, server_default=func.now())
    created_at    = Column(DateTime, server_default=func.now())
    updated_at    = Column(DateTime, server_default=func.now(), onupdate=func.now())

    brand = relationship("Brand")


# ---------- 内部周报（已并入 brand_metrics，保留 Out 模型供 API 兼容） ----------

# ---------- 情报预警 ----------
class IntelAlert(Base):
    __tablename__ = "intel_alerts"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    brand_id      = Column(Integer, ForeignKey("brands.id", ondelete="SET NULL"), nullable=True)
    news_id       = Column(Integer, ForeignKey("intel_news.id", ondelete="SET NULL"), nullable=True)
    metrics_id    = Column(Integer, ForeignKey("brand_metrics.id", ondelete="SET NULL"), nullable=True, comment="关联 brand_metrics 周报")
    visit_id      = Column(Integer, ForeignKey("visits.id", ondelete="SET NULL"), nullable=True)
    priority      = Column(Enum("P0", "P1", "P2", "P3"), nullable=False, default="P2")
    category      = Column(Enum("增长机会", "风险预警"), nullable=True, comment="情报分类")
    title         = Column(String(255), nullable=False)
    description   = Column(Text)
    suggestion    = Column(Text)
    ai_analysis   = Column(Text)
    ai_confidence = Column(Numeric(3, 2))
    status        = Column(Enum("pending", "confirmed", "linked", "closed"), nullable=False, default="pending")
    assignee      = Column(String(32))
    created_at    = Column(DateTime, server_default=func.now())
    updated_at    = Column(DateTime, server_default=func.now(), onupdate=func.now())

    brand = relationship("Brand")
    news  = relationship("IntelNews")
    visit = relationship("Visit")
    metrics = relationship("BrandMetrics")


class IntelBriefingCache(Base):
    """M2：简报缓存（30min TTL）"""
    __tablename__ = "intel_briefing_cache"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    brand_id      = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    briefing_data = Column(JSON, default=None)
    llm_summary     = Column(Text, comment="M3: LLM 生成的简报摘要")
    llm_generated_at = Column(DateTime, comment="M3: LLM 摘要生成时间")
    generated_at  = Column(DateTime, server_default=func.now())
    expires_at    = Column(DateTime)
    created_at    = Column(DateTime, server_default=func.now())
    updated_at    = Column(DateTime, server_default=func.now(), onupdate=func.now())

    brand = relationship("Brand")


# ---------- M3 登录 / 权限 ----------
class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    username      = Column(String(64), nullable=False, unique=True)
    password_hash = Column(String(128), nullable=False)
    password_algo = Column(
        Enum("sha256", "bcrypt"),
        nullable=False,
        default="sha256",
        comment="M5: 密码哈希算法",
    )
    display_name  = Column(String(64), nullable=False)
    dept          = Column(String(128), nullable=True, comment="M5: 部门展示")
    role          = Column(
        Enum("admin", "bd", "manager", "readonly"),
        nullable=False,
        default="bd",
        comment="admin=全品牌；manager=团队；bd=负责品牌",
    )
    is_active     = Column(Boolean, default=True)
    must_change_password = Column(Boolean, default=False, comment="M5: 强制改密")
    created_at    = Column(DateTime, server_default=func.now())
    updated_at    = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime, nullable=True, comment="M5: 最近登录")

    brands   = relationship("UserBrand", back_populates="user", lazy="selectin")
    sessions = relationship("UserSession", back_populates="user", lazy="selectin")


class UserBrand(Base):
    __tablename__ = "user_brands"

    id       = Column(Integer, primary_key=True, autoincrement=True)
    user_id  = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    brand_id = Column(INTEGER(unsigned=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user  = relationship("User", back_populates="brands")
    brand = relationship("Brand")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token      = Column(String(128), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="sessions")


class DwImportBatch(Base):
    __tablename__ = "dw_import_batch"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    batch_key     = Column(String(36), nullable=False, unique=True)
    source        = Column(Enum("csv", "api", "manual", "bi_csv", "dts"), nullable=False, default="csv")
    source_name   = Column(String(255))
    status        = Column(Enum("running", "success", "partial", "failed"), nullable=False, default="running")
    total_rows    = Column(Integer, nullable=False, default=0)
    inserted      = Column(Integer, nullable=False, default=0)
    updated       = Column(Integer, nullable=False, default=0)
    skipped       = Column(Integer, nullable=False, default=0)
    failed        = Column(Integer, nullable=False, default=0)
    error_summary = Column(Text)
    started_at    = Column(DateTime, server_default=func.now())
    finished_at   = Column(DateTime)
    created_at    = Column(DateTime, server_default=func.now())

    logs = relationship("SyncLog", back_populates="batch", cascade="all, delete-orphan")


class SyncLog(Base):
    __tablename__ = "sync_log"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    batch_id     = Column(Integer, ForeignKey("dw_import_batch.id", ondelete="CASCADE"), nullable=False)
    brand_id     = Column(Integer)  # brands.id 为 UNSIGNED，ORM 不写 FK 避免类型冲突
    name_key     = Column(String(32))
    period_value = Column(String(16))
    action       = Column(Enum("insert", "update", "skip", "error"), nullable=False)
    message      = Column(String(512))
    created_at   = Column(DateTime, server_default=func.now())

    batch = relationship("DwImportBatch", back_populates="logs")


class LlmCallLog(Base):
    __tablename__ = "llm_call_log"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(Integer, comment="users.id")
    username   = Column(String(64))
    route      = Column(String(128), nullable=False)
    status     = Column(
        Enum("success", "fallback", "quota", "error", "disabled"),
        nullable=False,
        default="success",
    )
    tokens_est = Column(Integer)
    latency_ms = Column(Integer)
    message    = Column(String(512))
    created_at = Column(DateTime, server_default=func.now())
