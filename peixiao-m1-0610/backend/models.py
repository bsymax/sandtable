"""
SQLAlchemy ORM 模型定义
对应 schema.sql 中的 7 张表
"""

from datetime import date, time, datetime
from typing import Optional, List

from sqlalchemy import (
    Column, Integer, String, Text, Date, Time, DateTime, Enum,
    ForeignKey, Boolean, func,
)
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


# ---------- 品牌联系人 ----------
class BrandContact(Base):
    __tablename__ = "brand_contacts"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    brand_id         = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    name             = Column(String(32), nullable=False)
    title            = Column(String(64))
    role_tag         = Column(Enum("决策者", "日常对接", "需加强", "其他"), default="日常对接")
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
