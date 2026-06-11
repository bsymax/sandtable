"""
SQLAlchemy ORM 模型
品牌档案模块：读取培翛公共表 + 佳璇新建表
"""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime, Enum,
    ForeignKey, Boolean, Numeric, func,
)
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


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

    contacts = relationship("BrandContact", back_populates="brand", lazy="selectin")
    profile  = relationship("BrandProfile", back_populates="brand", uselist=False, lazy="selectin")
    metrics  = relationship("BrandMetrics", back_populates="brand", lazy="selectin")


class BrandContact(Base):
    __tablename__ = "brand_contacts"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    brand_id          = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    name              = Column(String(32), nullable=False)
    title             = Column(String(64))
    role_tag          = Column(Enum("决策者", "日常对接", "需加强", "其他"), default="日常对接")
    phone             = Column(String(20))
    wechat            = Column(String(32))
    last_contact_date = Column(Date)
    is_active         = Column(Boolean, default=True)
    created_at        = Column(DateTime, server_default=func.now())
    updated_at        = Column(DateTime, server_default=func.now(), onupdate=func.now())

    brand = relationship("Brand", back_populates="contacts")


class BrandProfile(Base):
    __tablename__ = "brand_profiles"

    id               = Column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    brand_id         = Column(INTEGER(unsigned=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    founded_year     = Column(String(16))
    hq               = Column(String(64))
    positioning      = Column(String(255))
    org_structure    = Column(Text)
    taboos           = Column(Text)
    taboo_updated_by = Column(String(32))
    taboo_updated_at = Column(DateTime)
    created_at       = Column(DateTime, server_default=func.now())
    updated_at       = Column(DateTime, server_default=func.now(), onupdate=func.now())

    brand = relationship("Brand", back_populates="profile")


class BrandMetrics(Base):
    __tablename__ = "brand_metrics"

    id                    = Column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    brand_id              = Column(INTEGER(unsigned=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    period_type           = Column(Enum("weekly", "monthly"), nullable=False, default="weekly")
    period_value          = Column(String(16), nullable=False)
    gmv                   = Column(Numeric(12, 2))
    gmv_wow               = Column(Numeric(6, 2))
    gmv_yoy               = Column(Numeric(6, 2))
    orders                = Column(Integer)
    orders_wow            = Column(Numeric(6, 2))
    jd_share              = Column(Numeric(5, 2))
    jd_share_wow          = Column(Numeric(5, 2))
    tmall_share           = Column(Numeric(5, 2))
    douyin_share          = Column(Numeric(5, 2))
    pdd_share             = Column(Numeric(5, 2))
    channel_growth_jd     = Column(Numeric(5, 2))
    channel_growth_tmall  = Column(Numeric(5, 2))
    channel_growth_douyin = Column(Numeric(5, 2))
    category_distribution = Column(Text)
    category_share        = Column(Text)
    sku_count             = Column(Integer)
    p0_gap_count          = Column(Integer)
    gross_margin          = Column(Numeric(5, 2))
    uv_conversion         = Column(Numeric(5, 2))
    ad_rate               = Column(Numeric(5, 2))
    created_at            = Column(DateTime, server_default=func.now())
    updated_at            = Column(DateTime, server_default=func.now(), onupdate=func.now())

    brand = relationship("Brand", back_populates="metrics")
