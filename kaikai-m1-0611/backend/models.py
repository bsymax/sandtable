"""
SQLAlchemy ORM 模型定义 · 情报模块
"""
from datetime import date, time, datetime
from sqlalchemy import (
    Column, Integer, String, Text, Date, Time, DateTime, Enum,
    ForeignKey, Boolean, func,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# ---- 品牌（公共表，只读引用）----
class Brand(Base):
    __tablename__ = "brands"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    name          = Column(String(64), nullable=False)
    name_key      = Column(String(32), nullable=False, unique=True)
    level         = Column(Enum("S", "A", "B", "C"), nullable=False, default="B")
    responsible   = Column(String(32))
    archive_score = Column(Integer, default=0)
    relation_temp = Column(Integer, default=50)
    baseline_freq = Column(String(32), default="季度/次")
    status        = Column(Enum("active", "inactive"), nullable=False, default="active")
    created_at    = Column(DateTime, server_default=func.now())
    updated_at    = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ---- 拜访（公共表，只读引用）----
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
    record_id  = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    brand = relationship("Brand")


# ================================================================
# 情报模块 · 专有表
# ================================================================

# ---- 外部新闻/资讯 ----
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
    url_fingerprint = Column(String(64))
    published_at  = Column(DateTime)
    fetched_at    = Column(DateTime, server_default=func.now())
    created_at    = Column(DateTime, server_default=func.now())
    updated_at    = Column(DateTime, server_default=func.now(), onupdate=func.now())

    brand = relationship("Brand")


# ---- 内部周报 ----
class IntelWeeklyReport(Base):
    __tablename__ = "intel_weekly_reports"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    brand_id         = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    week_start       = Column(Date, nullable=False)
    week_end         = Column(Date, nullable=False)
    week_label       = Column(String(16))
    weekly_gmv       = Column(Integer)
    gmv_change       = Column(Integer)
    competitor_moves = Column(Text)
    inventory_status = Column(Text)
    risk_points      = Column(Text)
    opportunities    = Column(Text)
    next_week_plan   = Column(Text)
    reporter         = Column(String(32))
    status           = Column(Enum("draft", "submitted"), default="draft")
    created_at       = Column(DateTime, server_default=func.now())
    updated_at       = Column(DateTime, server_default=func.now(), onupdate=func.now())

    brand = relationship("Brand")


# ---- 情报预警 ----
class IntelAlert(Base):
    __tablename__ = "intel_alerts"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    brand_id      = Column(Integer, ForeignKey("brands.id", ondelete="SET NULL"), nullable=True)
    news_id       = Column(Integer, ForeignKey("intel_news.id", ondelete="SET NULL"), nullable=True)
    weekly_id     = Column(Integer, ForeignKey("intel_weekly_reports.id", ondelete="SET NULL"), nullable=True)
    visit_id      = Column(Integer, ForeignKey("visits.id", ondelete="SET NULL"), nullable=True)
    priority      = Column(Enum("P0", "P1", "P2", "P3"), nullable=False, default="P2")
    title         = Column(String(255), nullable=False)
    description   = Column(Text)
    suggestion    = Column(Text)
    ai_analysis   = Column(Text)
    ai_confidence = Column(Integer)
    status        = Column(Enum("pending", "confirmed", "linked", "closed"), nullable=False, default="pending")
    assignee      = Column(String(32))
    created_at    = Column(DateTime, server_default=func.now())
    updated_at    = Column(DateTime, server_default=func.now(), onupdate=func.now())

    brand = relationship("Brand")
    news  = relationship("IntelNews")
    visit = relationship("Visit")
    weekly_report = relationship("IntelWeeklyReport")
