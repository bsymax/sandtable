#!/usr/bin/env python3
"""
品牌沙盘 M1 · 京东云一键部署脚本
适配: Ubuntu 24.04 / 4核16G / Python 3.12
用 root 执行: python3 deploy.py
"""
import subprocess, os, sys, random, string, shutil, time
from pathlib import Path

RED = '\033[31m'; GREEN = '\033[32m'; YELLOW = '\033[33m'; NC = '\033[0m'
def info(msg):  print(f"{GREEN}[INFO]{NC}  {msg}")
def warn(msg):  print(f"{YELLOW}[WARN]{NC}  {msg}")
def err(msg):   print(f"{RED}[ERROR]{NC} {msg}")

def run(cmd, check=True, shell=True):
    """执行 shell 命令并打印输出"""
    r = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
    if r.returncode != 0 and check:
        print(f"  [FAIL] {cmd[:80]}...")
        print(f"  stderr: {r.stderr.strip()[:200]}")
        if check:
            sys.exit(1)
    return r

# ==============================
DB_ROOT_PASS = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
DB_APP_PASS  = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
APP_DIR = "/opt/brand-sandtable"
APP_PORT = 8000

info("==============================================")
info("  品牌沙盘 M1 · 自动部署")
info("==============================================")

# === Step 1: 系统依赖 ===
info("Step 1/7: 安装系统依赖 (apt-get)...")
run("apt-get update -qq")
run("apt-get install -y -qq python3 python3-pip python3-venv mysql-server mysql-client nginx curl ufw git openssl")
info("依赖安装完成")

# === Step 2: MySQL ===
info("Step 2/7: 配置 MySQL...")
run("systemctl start mysql")
run("systemctl enable mysql")

# Ubuntu 24.04 MySQL 8.4: root 用 auth_socket，先改密码
result = subprocess.run("mysql -u root -e 'SELECT 1'", shell=True, capture_output=True, text=True)
if result.returncode != 0:
    err(f"MySQL 无法连接: {result.stderr}")
    sys.exit(1)

subprocess.run(
    f'mysql -u root -e "ALTER USER root@localhost IDENTIFIED WITH mysql_native_password BY \'{DB_ROOT_PASS}\'; FLUSH PRIVILEGES;"',
    shell=True, capture_output=True, text=True)

# 创建数据库和用户
run(f'mysql -u root -p"{DB_ROOT_PASS}" -e "CREATE DATABASE IF NOT EXISTS brand_sandtable DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci;" 2>/dev/null || mysql -u root -e "CREATE DATABASE IF NOT EXISTS brand_sandtable DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci;"')
run(f'mysql -u root -p"{DB_ROOT_PASS}" -e "CREATE USER IF NOT EXISTS brand_app@localhost IDENTIFIED BY \'{DB_APP_PASS}\'; GRANT ALL PRIVILEGES ON brand_sandtable.* TO brand_app@localhost; FLUSH PRIVILEGES;" 2>/dev/null || mysql -u root -e "CREATE USER IF NOT EXISTS brand_app@localhost IDENTIFIED BY \'{DB_APP_PASS}\'; GRANT ALL PRIVILEGES ON brand_sandtable.* TO brand_app@localhost; FLUSH PRIVILEGES;"')
info(f"  root 密码: {DB_ROOT_PASS}")
info(f"  app  密码: {DB_APP_PASS}")

# === Step 3: 写入项目文件 ===
info("Step 3/7: 写入项目文件...")
Path(APP_DIR).mkdir(parents=True, exist_ok=True)
for sub in ["backend", "frontend", "database"]:
    Path(APP_DIR, sub).mkdir(exist_ok=True)

# --- 写入配置文件 ---
Path(APP_DIR, "backend", "__init__.py").touch()

Path(APP_DIR, "backend", "config.py").write_text(f'''"""
数据库连接配置 & 应用设置
"""
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
load_dotenv()
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "brand_app")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "brand_sandtable")
DB_CHARSET = os.getenv("DB_CHARSET", "utf8mb4")
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
CORS_ORIGINS = ["*"]
DATABASE_URL = f"mysql+pymysql://{{DB_USER}}:{{quote_plus(DB_PASSWORD)}}@{{DB_HOST}}:{{DB_PORT}}/{{DB_NAME}}?charset={{DB_CHARSET}}"
''')

Path(APP_DIR, "backend", ".env").write_text(f'''DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=brand_app
DB_PASSWORD={DB_APP_PASS}
DB_NAME=brand_sandtable
DB_CHARSET=utf8mb4
SERVER_HOST=0.0.0.0
SERVER_PORT={APP_PORT}
CORS_ORIGINS=*
''')

Path(APP_DIR, "backend", "database.py").write_text('''"""
数据库会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from config import DATABASE_URL
engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20, pool_recycle=3600, echo=False)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try: yield db
    finally: db.close()
''')

Path(APP_DIR, "backend", "requirements.txt").write_text('''fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
pymysql>=1.1.0
cryptography>=41.0.0
python-dotenv>=1.0.0
pydantic>=2.5.0
''')

# --- 写入 models.py ---
Path(APP_DIR, "backend", "models.py").write_text('''"""
SQLAlchemy ORM 模型定义
"""
from datetime import date, time, datetime
from sqlalchemy import Column, Integer, String, Text, Date, Time, DateTime, Enum, ForeignKey, Boolean, func
from sqlalchemy.orm import declarative_base, relationship
Base = declarative_base()

class Brand(Base):
    __tablename__ = "brands"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)
    name_key = Column(String(32), nullable=False, unique=True)
    level = Column(Enum("S", "A", "B", "C"), nullable=False, default="B")
    responsible = Column(String(32))
    archive_score = Column(Integer, default=0)
    relation_temp = Column(Integer, default=50)
    baseline_freq = Column(String(32), default="季度/次")
    status = Column(Enum("active", "inactive"), nullable=False, default="active")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    contacts = relationship("BrandContact", back_populates="brand", lazy="selectin")
    visits = relationship("Visit", back_populates="brand", lazy="selectin")

class BrandContact(Base):
    __tablename__ = "brand_contacts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(32), nullable=False)
    title = Column(String(64))
    role_tag = Column(Enum("决策者", "日常对接", "需加强", "其他"), default="日常对接")
    phone = Column(String(20))
    wechat = Column(String(32))
    last_contact_date = Column(Date)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    brand = relationship("Brand", back_populates="contacts")

class Visit(Base):
    __tablename__ = "visits"
    id = Column(Integer, primary_key=True, autoincrement=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    visit_date = Column(Date, nullable=False)
    visit_time = Column(Time, default=time(14, 0))
    visit_type = Column(Enum("urgent", "regular", "renewal"), nullable=False, default="regular")
    purpose = Column(Text, nullable=False)
    notes = Column(Text)
    status = Column(Enum("scheduled", "completed", "cancelled"), nullable=False, default="scheduled")
    record_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    brand = relationship("Brand", back_populates="visits")
    attendees = relationship("VisitAttendee", back_populates="visit", lazy="selectin")
    record = relationship("VisitRecord", primaryjoin="foreign(Visit.id) == VisitRecord.visit_id", uselist=False, viewonly=True, sync_backref=False)
    commitments = relationship("Commitment", back_populates="visit", lazy="selectin")
    todos = relationship("Todo", back_populates="visit", lazy="selectin")

class VisitAttendee(Base):
    __tablename__ = "visit_attendees"
    id = Column(Integer, primary_key=True, autoincrement=True)
    visit_id = Column(Integer, ForeignKey("visits.id", ondelete="CASCADE"), nullable=False)
    contact_id = Column(Integer, ForeignKey("brand_contacts.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(32), nullable=False)
    role = Column(Enum("bd", "brand"), default="bd")
    created_at = Column(DateTime, server_default=func.now())
    visit = relationship("Visit", back_populates="attendees")
    contact = relationship("BrandContact")

class VisitRecord(Base):
    __tablename__ = "visit_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    visit_id = Column(Integer, ForeignKey("visits.id", ondelete="CASCADE"), unique=True, nullable=False)
    participants = Column(Text)
    topics = Column(Text)
    commitments_raw = Column(Text)
    undone_items = Column(Text)
    relation_change = Column(Enum("up", "flat", "down"), default="flat")
    next_visit_date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    visit = relationship("Visit", foreign_keys=[visit_id])
    commit = relationship("Commitment", back_populates="record", lazy="selectin")
    todos = relationship("Todo", back_populates="record", lazy="selectin")

class Commitment(Base):
    __tablename__ = "commitments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    visit_id = Column(Integer, ForeignKey("visits.id", ondelete="CASCADE"), nullable=False)
    record_id = Column(Integer, ForeignKey("visit_records.id", ondelete="SET NULL"))
    content = Column(String(255), nullable=False)
    party = Column(Enum("brand", "bd"), default="brand")
    status = Column(Enum("pending", "fulfilled", "broken"), nullable=False, default="pending")
    deadline = Column(Date)
    fulfilled_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    visit = relationship("Visit", back_populates="commitments")
    record = relationship("VisitRecord", back_populates="commit")

class Todo(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(Integer, ForeignKey("visit_records.id", ondelete="SET NULL"))
    visit_id = Column(Integer, ForeignKey("visits.id", ondelete="SET NULL"))
    priority = Column(Enum("P0", "P1", "P2", "P3"), nullable=False, default="P2")
    title = Column(String(255), nullable=False)
    deadline = Column(Date)
    assignee = Column(String(32))
    status = Column(Enum("pending", "done", "overdue"), nullable=False, default="pending")
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
    visit = relationship("Visit", back_populates="todos")
    record = relationship("VisitRecord", back_populates="todos")
''')

# --- 写入 schemas.py ---
Path(APP_DIR, "backend", "schemas.py").write_text('''"""
Pydantic 请求/响应模型
"""
from datetime import date, time, datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class BrandOut(BaseModel):
    id: int; name: str; name_key: str; level: str; responsible: Optional[str] = None
    archive_score: int; relation_temp: int; baseline_freq: Optional[str] = None
    status: str; created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    class Config: from_attributes = True

class BrandBrief(BaseModel):
    id: int; name: str; name_key: str; level: str
    class Config: from_attributes = True

class ContactOut(BaseModel):
    id: int; brand_id: int; name: str; title: Optional[str] = None
    role_tag: Optional[str] = None; phone: Optional[str] = None; wechat: Optional[str] = None
    last_contact_date: Optional[date] = None; is_active: bool
    class Config: from_attributes = True

class VisitCreate(BaseModel):
    brand_id: int; visit_date: date; visit_time: Optional[time] = time(14, 0)
    visit_type: str = "regular"; purpose: str; notes: Optional[str] = None
    attendee_names: List[str] = []

class VisitAttendeeOut(BaseModel):
    id: int; name: str; role: str; contact_id: Optional[int] = None
    class Config: from_attributes = True

class VisitOut(BaseModel):
    id: int; brand_id: int; brand_name: Optional[str] = None; brand_level: Optional[str] = None
    visit_date: date; visit_time: Optional[time] = None; visit_type: str; purpose: str
    notes: Optional[str] = None; status: str; record_id: Optional[int] = None
    attendees: List[VisitAttendeeOut] = []
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    class Config: from_attributes = True

class VisitUpdate(BaseModel):
    visit_date: Optional[date] = None; visit_time: Optional[time] = None
    visit_type: Optional[str] = None; purpose: Optional[str] = None
    notes: Optional[str] = None; status: Optional[str] = None

class RecordCreate(BaseModel):
    visit_id: int; participants: Optional[str] = None; topics: Optional[str] = None
    commitments_raw: Optional[str] = None; undone_items: Optional[str] = None
    relation_change: str = "flat"; next_visit_date: Optional[date] = None; todos: List[dict] = []

class RecordOut(BaseModel):
    id: int; visit_id: int; participants: Optional[str] = None; topics: Optional[str] = None
    commitments_raw: Optional[str] = None; undone_items: Optional[str] = None
    relation_change: Optional[str] = None; next_visit_date: Optional[date] = None
    visit_date: Optional[date] = None; brand_name: Optional[str] = None
    brand_level: Optional[str] = None; visit_type: Optional[str] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    class Config: from_attributes = True

class CommitmentOut(BaseModel):
    id: int; visit_id: int; record_id: Optional[int] = None; content: str; party: str
    status: str; deadline: Optional[date] = None; fulfilled_at: Optional[datetime] = None
    class Config: from_attributes = True

class CommitmentUpdate(BaseModel):
    status: Optional[str] = None; deadline: Optional[date] = None

class TodoOut(BaseModel):
    id: int; record_id: Optional[int] = None; visit_id: Optional[int] = None
    priority: str; title: str; deadline: Optional[date] = None; assignee: Optional[str] = None
    status: str; created_at: Optional[datetime] = None; completed_at: Optional[datetime] = None
    class Config: from_attributes = True

class TodoUpdate(BaseModel):
    status: Optional[str] = None; priority: Optional[str] = None

class HealthItem(BaseModel):
    brand_id: int; brand_name: str; name_key: str; level: str; baseline_freq: str
    visit_count_90d: int = 0; status_label: str = "达标"; status_level: str = "green"

class ApiResponse(BaseModel):
    success: bool = True; message: str = "ok"; data: Optional[dict] = None
''')

# --- 写入 main.py ---
Path(APP_DIR, "backend", "main.py").write_text('''"""
FastAPI 主应用 —— 智能拜访助手 API
"""
from datetime import date, time, datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, case
from config import CORS_ORIGINS, SERVER_HOST, SERVER_PORT
from database import get_db, engine
from models import Base, Brand, BrandContact, Visit, VisitAttendee, VisitRecord, Commitment, Todo
from schemas import (
    BrandOut, BrandBrief, ContactOut,
    VisitCreate, VisitOut, VisitUpdate, VisitAttendeeOut,
    RecordCreate, RecordOut, CommitmentOut, CommitmentUpdate,
    TodoOut, TodoUpdate, HealthItem, ApiResponse,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="品牌沙盘 M1 · 智能拜访助手 API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

@app.get("/api/brands", response_model=List[BrandBrief], tags=["品牌"])
def list_brands(db: Session = Depends(get_db)):
    return db.query(Brand).filter(Brand.status == "active").order_by(
        case((Brand.level == "S", 0), (Brand.level == "A", 1), (Brand.level == "B", 2), else_=3)).all()

@app.get("/api/brands/detail", response_model=List[BrandOut], tags=["品牌"])
def list_brands_detail(db: Session = Depends(get_db)):
    return db.query(Brand).filter(Brand.status == "active").order_by(Brand.id).all()

@app.get("/api/brands/{name_key}", response_model=BrandOut, tags=["品牌"])
def get_brand(name_key: str, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.name_key == name_key, Brand.status == "active").first()
    if not brand: raise HTTPException(404, "品牌不存在")
    return brand

@app.get("/api/brands/{brand_id}/contacts", response_model=List[ContactOut], tags=["联系人"])
def list_contacts(brand_id: int, db: Session = Depends(get_db)):
    return db.query(BrandContact).filter(BrandContact.brand_id == brand_id, BrandContact.is_active == True).all()

@app.post("/api/visits", response_model=VisitOut, tags=["拜访"])
def create_visit(payload: VisitCreate, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.id == payload.brand_id).first()
    if not brand: raise HTTPException(404, "品牌不存在")
    visit = Visit(brand_id=payload.brand_id, visit_date=payload.visit_date, visit_time=payload.visit_time or time(14, 0), visit_type=payload.visit_type, purpose=payload.purpose, notes=payload.notes, status="scheduled")
    db.add(visit); db.flush()
    for name in payload.attendee_names:
        if name.strip(): db.add(VisitAttendee(visit_id=visit.id, name=name.strip(), role="brand"))
    db.commit(); db.refresh(visit)
    return _format_visit(visit, brand)

@app.get("/api/visits", response_model=List[VisitOut], tags=["拜访"])
def list_visits(status: Optional[str] = None, brand_id: Optional[int] = None, month: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Visit)
    if status: q = q.filter(Visit.status == status)
    if brand_id: q = q.filter(Visit.brand_id == brand_id)
    if month: q = q.filter(func.date_format(Visit.visit_date, "%Y-%m") == month)
    q = q.order_by(desc(Visit.visit_date))
    return [_format_visit(v, v.brand) for v in q.all()]

@app.get("/api/visits/{visit_id}", response_model=VisitOut, tags=["拜访"])
def get_visit(visit_id: int, db: Session = Depends(get_db)):
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit: raise HTTPException(404, "拜访不存在")
    return _format_visit(visit, visit.brand)

@app.put("/api/visits/{visit_id}", response_model=VisitOut, tags=["拜访"])
def update_visit(visit_id: int, payload: VisitUpdate, db: Session = Depends(get_db)):
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit: raise HTTPException(404, "拜访不存在")
    for k, v in payload.dict(exclude_unset=True).items(): setattr(visit, k, v)
    db.commit(); db.refresh(visit)
    return _format_visit(visit, visit.brand)

@app.delete("/api/visits/{visit_id}", response_model=ApiResponse, tags=["拜访"])
def delete_visit(visit_id: int, db: Session = Depends(get_db)):
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit: raise HTTPException(404, "拜访不存在")
    db.delete(visit); db.commit()
    return ApiResponse(message="拜访已删除")

@app.post("/api/records", response_model=RecordOut, tags=["拜访记录"])
def create_record(payload: RecordCreate, db: Session = Depends(get_db)):
    visit = db.query(Visit).filter(Visit.id == payload.visit_id).first()
    if not visit: raise HTTPException(404, "拜访不存在")
    existing = db.query(VisitRecord).filter(VisitRecord.visit_id == payload.visit_id).first()
    if existing: raise HTTPException(400, "该拜访已有记录")
    record = VisitRecord(visit_id=payload.visit_id, participants=payload.participants, topics=payload.topics, commitments_raw=payload.commitments_raw, undone_items=payload.undone_items, relation_change=payload.relation_change, next_visit_date=payload.next_visit_date)
    db.add(record); db.flush()
    visit.status = "completed"; visit.record_id = record.id
    for td in payload.todos:
        db.add(Todo(record_id=record.id, visit_id=payload.visit_id, priority=td.get("priority", "P2"), title=td.get("title", ""), deadline=_parse_date(td.get("deadline")), assignee=td.get("assignee", visit.brand.responsible if visit.brand else "采销")))
    if not payload.todos:
        for td in [{"priority": "P0", "title": "跟进联合投放方案确认", "days": 2}, {"priority": "P0", "title": "跟进新品排期确认", "days": 5}, {"priority": "P1", "title": "确认对方人员变动情况", "days": 10}, {"priority": "P2", "title": "下次拜访准备", "days": 12}]:
            db.add(Todo(record_id=record.id, visit_id=payload.visit_id, priority=td["priority"], title=td["title"], deadline=(visit.visit_date + timedelta(days=td["days"])) if visit.visit_date else None, assignee=visit.brand.responsible if visit.brand else "采销"))
    db.commit(); db.refresh(record)
    return _format_record(record, visit)

@app.get("/api/records", response_model=List[RecordOut], tags=["拜访记录"])
def list_records(brand_id: Optional[int] = None, limit: int = 20, db: Session = Depends(get_db)):
    q = db.query(VisitRecord).join(Visit).order_by(desc(VisitRecord.created_at))
    if brand_id: q = q.filter(Visit.brand_id == brand_id)
    return [_format_record(r, r.visit) for r in q.limit(limit).all()]

@app.get("/api/records/{record_id}", response_model=RecordOut, tags=["拜访记录"])
def get_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(VisitRecord).filter(VisitRecord.id == record_id).first()
    if not record: raise HTTPException(404, "记录不存在")
    return _format_record(record, record.visit)

@app.get("/api/commitments", response_model=List[CommitmentOut], tags=["承诺"])
def list_commitments(visit_id: Optional[int] = None, status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Commitment)
    if visit_id: q = q.filter(Commitment.visit_id == visit_id)
    if status: q = q.filter(Commitment.status == status)
    return q.order_by(desc(Commitment.created_at)).all()

@app.put("/api/commitments/{commitment_id}", response_model=CommitmentOut, tags=["承诺"])
def update_commitment(commitment_id: int, payload: CommitmentUpdate, db: Session = Depends(get_db)):
    c = db.query(Commitment).filter(Commitment.id == commitment_id).first()
    if not c: raise HTTPException(404, "承诺不存在")
    if payload.status:
        c.status = payload.status
        if payload.status == "fulfilled": c.fulfilled_at = datetime.now()
    if payload.deadline: c.deadline = payload.deadline
    db.commit(); db.refresh(c)
    return c

@app.get("/api/todos", response_model=List[TodoOut], tags=["待办"])
def list_todos(status: Optional[str] = None, priority: Optional[str] = None, assignee: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Todo)
    if status: q = q.filter(Todo.status == status)
    if priority: q = q.filter(Todo.priority == priority)
    if assignee: q = q.filter(Todo.assignee == assignee)
    return q.order_by(case((Todo.priority == "P0", 0), (Todo.priority == "P1", 1), else_=2), Todo.deadline.asc()).all()

@app.put("/api/todos/{todo_id}", response_model=TodoOut, tags=["待办"])
def update_todo(todo_id: int, payload: TodoUpdate, db: Session = Depends(get_db)):
    t = db.query(Todo).filter(Todo.id == todo_id).first()
    if not t: raise HTTPException(404, "待办不存在")
    if payload.status:
        t.status = payload.status
        if payload.status == "done": t.completed_at = datetime.now()
    if payload.priority: t.priority = payload.priority
    db.commit(); db.refresh(t)
    return t

@app.get("/api/health", response_model=List[HealthItem], tags=["健康度"])
def visit_health(db: Session = Depends(get_db)):
    brands = db.query(Brand).filter(Brand.status == "active").all()
    ninety_days_ago = date.today() - timedelta(days=90)
    result = []
    for brand in brands:
        count = db.query(func.count(Visit.id)).filter(Visit.brand_id == brand.id, Visit.status == "completed", Visit.visit_date >= ninety_days_ago).scalar() or 0
        if brand.level == "S": healthy = count >= 3; label = "达标" if healthy else ("偏低" if count >= 1 else "严重偏低")
        elif brand.level == "A": healthy = count >= 1; label = "达标" if healthy else "偏低"
        else: healthy = count >= 1; label = "达标" if healthy else "严重偏低"
        result.append(HealthItem(brand_id=brand.id, brand_name=brand.name, name_key=brand.name_key, level=brand.level, baseline_freq=brand.baseline_freq or "季度/次", visit_count_90d=count, status_label=label, status_level="green" if healthy else ("amber" if count > 0 else "red")))
    return result

@app.get("/api/brands/{name_key}/reminder", tags=["拜访提醒"])
def brand_visit_reminder(name_key: str, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.name_key == name_key).first()
    if not brand: raise HTTPException(404, "品牌不存在")
    last_visit = db.query(Visit).filter(Visit.brand_id == brand.id, Visit.status == "completed").order_by(desc(Visit.visit_date)).first()
    pending = db.query(Commitment).filter(Commitment.visit.has(Visit.brand_id == brand.id), Commitment.status == "pending").all()
    stale = db.query(BrandContact).filter(BrandContact.brand_id == brand.id, BrandContact.last_contact_date < date.today() - timedelta(days=30)).all()
    return {"brand": brand.name, "level": brand.level, "relation_temp": brand.relation_temp, "archive_score": brand.archive_score, "last_visit_date": last_visit.visit_date if last_visit else None, "last_visit_purpose": last_visit.purpose if last_visit else None, "pending_commitments": [{"content": c.content, "deadline": c.deadline} for c in pending], "stale_contacts": [{"name": c.name, "days_since": (date.today() - c.last_contact_date).days} for c in stale], "days_since_last_visit": (date.today() - last_visit.visit_date).days if last_visit else 999}

def _format_visit(visit, brand=None):
    return VisitOut(id=visit.id, brand_id=visit.brand_id, brand_name=brand.name if brand else None, brand_level=brand.level if brand else None, visit_date=visit.visit_date, visit_time=visit.visit_time, visit_type=visit.visit_type, purpose=visit.purpose, notes=visit.notes, status=visit.status, record_id=visit.record_id, attendees=[VisitAttendeeOut(id=a.id, name=a.name, role=a.role, contact_id=a.contact_id) for a in (visit.attendees or [])], created_at=visit.created_at, updated_at=visit.updated_at)

def _format_record(record, visit=None):
    return RecordOut(id=record.id, visit_id=record.visit_id, participants=record.participants, topics=record.topics, commitments_raw=record.commitments_raw, undone_items=record.undone_items, relation_change=record.relation_change, next_visit_date=record.next_visit_date, visit_date=visit.visit_date if visit else None, brand_name=visit.brand.name if visit and visit.brand else None, brand_level=visit.brand.level if visit and visit.brand else None, visit_type=visit.visit_type if visit else None, created_at=record.created_at, updated_at=record.updated_at)

def _parse_date(val):
    if val is None: return None
    if isinstance(val, date): return val
    try: return datetime.strptime(str(val)[:10], "%Y-%m-%d").date()
    except: return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=SERVER_HOST, port=SERVER_PORT, reload=False)
''')

# --- 写入 schema.sql ---
Path(APP_DIR, "database", "schema.sql").write_text('''-- 品牌沙盘 M1 数据库建表 + 种子数据
CREATE DATABASE IF NOT EXISTS brand_sandtable DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci;
USE brand_sandtable;

CREATE TABLE IF NOT EXISTS brands (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(64) NOT NULL,
  name_key VARCHAR(32) NOT NULL UNIQUE,
  level ENUM('S','A','B','C') NOT NULL DEFAULT 'B',
  responsible VARCHAR(32) DEFAULT NULL,
  archive_score INT DEFAULT 0,
  relation_temp INT DEFAULT 50,
  baseline_freq VARCHAR(32) DEFAULT '季度/次',
  status ENUM('active','inactive') NOT NULL DEFAULT 'active',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS brand_contacts (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  brand_id INT UNSIGNED NOT NULL,
  name VARCHAR(32) NOT NULL,
  title VARCHAR(64) DEFAULT NULL,
  role_tag ENUM('决策者','日常对接','需加强','其他') DEFAULT '日常对接',
  phone VARCHAR(20) DEFAULT NULL,
  wechat VARCHAR(32) DEFAULT NULL,
  last_contact_date DATE DEFAULT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS visits (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  brand_id INT UNSIGNED NOT NULL,
  visit_date DATE NOT NULL,
  visit_time TIME DEFAULT '14:00:00',
  visit_type ENUM('urgent','regular','renewal') NOT NULL DEFAULT 'regular',
  purpose TEXT NOT NULL,
  notes TEXT DEFAULT NULL,
  status ENUM('scheduled','completed','cancelled') NOT NULL DEFAULT 'scheduled',
  record_id INT UNSIGNED DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS visit_attendees (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  visit_id INT UNSIGNED NOT NULL,
  contact_id INT UNSIGNED DEFAULT NULL,
  name VARCHAR(32) NOT NULL,
  role VARCHAR(16) DEFAULT 'bd',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (visit_id) REFERENCES visits(id) ON DELETE CASCADE,
  FOREIGN KEY (contact_id) REFERENCES brand_contacts(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS visit_records (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  visit_id INT UNSIGNED UNIQUE NOT NULL,
  participants TEXT DEFAULT NULL,
  topics TEXT DEFAULT NULL,
  commitments_raw TEXT DEFAULT NULL,
  undone_items TEXT DEFAULT NULL,
  relation_change ENUM('up','flat','down') DEFAULT 'flat',
  next_visit_date DATE DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (visit_id) REFERENCES visits(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS commitments (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  visit_id INT UNSIGNED NOT NULL,
  record_id INT UNSIGNED DEFAULT NULL,
  content VARCHAR(255) NOT NULL,
  party ENUM('brand','bd') DEFAULT 'brand',
  status ENUM('pending','fulfilled','broken') NOT NULL DEFAULT 'pending',
  deadline DATE DEFAULT NULL,
  fulfilled_at DATETIME DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (visit_id) REFERENCES visits(id) ON DELETE CASCADE,
  FOREIGN KEY (record_id) REFERENCES visit_records(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS todos (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  record_id INT UNSIGNED DEFAULT NULL,
  visit_id INT UNSIGNED DEFAULT NULL,
  priority ENUM('P0','P1','P2','P3') NOT NULL DEFAULT 'P2',
  title VARCHAR(255) NOT NULL,
  deadline DATE DEFAULT NULL,
  assignee VARCHAR(32) DEFAULT NULL,
  status ENUM('pending','done','overdue') NOT NULL DEFAULT 'pending',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at DATETIME DEFAULT NULL,
  FOREIGN KEY (visit_id) REFERENCES visits(id) ON DELETE SET NULL,
  FOREIGN KEY (record_id) REFERENCES visit_records(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 种子数据
INSERT IGNORE INTO brands (id, name, name_key, level, responsible, archive_score, relation_temp, baseline_freq) VALUES
(1, '美的', 'midea', 'S', '周采销', 88, 72, '2-4周/次'),
(2, '九阳', 'joyoung', 'A', '吴采销', 85, 85, '季度/次'),
(3, '苏泊尔', 'supor', 'A', '陈采销', 78, 68, '季度/次'),
(4, '小熊电器', 'bear', 'B', '李采销', 81, 88, '季度/次'),
(5, '摩飞', 'morphy', 'B', '王采销', 71, 65, '季度/次');

INSERT IGNORE INTO brand_contacts (id, brand_id, name, title, role_tag, last_contact_date) VALUES
(1, 1, '王建国', '电商事业部总经理', '决策者', '2026-06-05'),
(2, 1, '李敏', '京东渠道运营总监', '日常对接', '2026-06-05'),
(3, 1, '张磊', '产品总监', '需加强', '2026-05-15'),
(4, 2, '陈志远', '电商VP', '决策者', '2026-05-20'),
(5, 2, '赵雪', '京东渠道经理', '日常对接', '2026-05-28'),
(6, 3, '刘明', '电商总监', '决策者', '2026-04-25'),
(7, 4, '孙悦', '电商经理', '日常对接', '2026-06-01');

INSERT IGNORE INTO visits (id, brand_id, visit_date, visit_time, visit_type, purpose, status) VALUES
(1, 1, '2026-06-10', '14:00:00', 'urgent', '618投放+新品', 'scheduled'),
(2, 1, '2026-06-05', '10:00:00', 'regular', '季度对齐', 'completed'),
(3, 2, '2026-05-20', '15:00:00', 'regular', '季度复盘', 'completed'),
(4, 2, '2026-06-18', '14:00:00', 'regular', '例行拜访', 'scheduled'),
(5, 3, '2026-06-25', '10:00:00', 'regular', 'Q2复盘+广告置换', 'scheduled'),
(6, 1, '2026-05-15', '10:00:00', 'regular', '产品沟通 · 空气炸锅Pro', 'completed');

INSERT IGNORE INTO visit_attendees (visit_id, contact_id, name, role) VALUES
(1, 1, '王建国', 'brand'), (1, 2, '李敏', 'brand'),
(2, 1, '王建国', 'brand'), (2, 2, '李敏', 'brand'),
(3, 4, '陈志远', 'brand'), (3, 5, '赵雪', 'brand');

INSERT IGNORE INTO visit_records (id, visit_id, participants, topics, commitments_raw, relation_change, next_visit_date) VALUES
(1, 2, '周采销；王建国、李敏', '618目标+新品首发', '- 3款新品JD首发\\n- 联合投放预算600万\\n- 空气炸锅Pro排期确认', 'flat', '2026-06-24'),
(2, 3, '吴采销；陈志远、赵雪', 'K9 Pro合作沟通', '- K9 Pro包销价确认\\n- 618库存锁定', 'up', '2026-07-10'),
(3, 6, '周采销；张磊', '空气炸锅Pro产品沟通', '- 1款空气炸锅JD首发', 'flat', '2026-05-30');

INSERT IGNORE INTO commitments (visit_id, record_id, content, party, status, deadline) VALUES
(2, 1, '3款新品JD首发', 'brand', 'broken', '2026-05-30'),
(2, 1, '联合投放预算600万', 'brand', 'pending', '2026-06-12'),
(2, 1, '空气炸锅Pro排期确认', 'brand', 'pending', '2026-06-15'),
(3, 2, 'K9 Pro包销价确认', 'brand', 'fulfilled', '2026-06-01'),
(3, 2, '618库存锁定', 'brand', 'pending', '2026-06-10'),
(6, 3, '1款空气炸锅JD首发', 'brand', 'fulfilled', '2026-05-30');

INSERT IGNORE INTO todos (record_id, visit_id, priority, title, deadline, assignee, status) VALUES
(1, 2, 'P0', '跟进600万投放方案确认', '2026-06-12', '周采销', 'pending'),
(1, 2, 'P0', '跟进空气炸锅Pro排期确认', '2026-06-15', '周采销', 'pending'),
(1, 2, 'P1', '确认王建国岗位变动情况', '2026-06-20', '周采销', 'pending'),
(1, 2, 'P2', '6/24下次拜访准备', '2026-06-22', '周采销', 'pending'),
(2, 3, 'P1', '跟进K9 Pro包销价', '2026-06-05', '吴采销', 'done'),
(2, 3, 'P2', '618库存方案确认', '2026-06-10', '吴采销', 'pending');
''')

info("项目文件写入完成")

# === Step 4: Python 环境 ===
info("Step 4/7: 安装 Python 依赖...")
os.chdir(f"{APP_DIR}/backend")
run("python3 -m venv venv")
venv_pip = f"{APP_DIR}/backend/venv/bin/pip"
venv_python = f"{APP_DIR}/backend/venv/bin/python"
run(f"{venv_pip} install --upgrade pip -q")
run(f"{venv_pip} install -r requirements.txt -q")
info("Python 依赖安装完成")

# === Step 5: 数据库初始化 ===
info("Step 5/7: 初始化数据库...")
run(f'mysql -u brand_app -p"{DB_APP_PASS}" brand_sandtable < {APP_DIR}/database/schema.sql 2>/dev/null || mysql -u root -e "SOURCE {APP_DIR}/database/schema.sql;"', check=False)
# SQLAlchemy 自动建表
run(f"cd {APP_DIR}/backend && {venv_python} -c 'from database import engine; from models import Base; Base.metadata.create_all(bind=engine); print(\"ORM表同步完成\")'")
info("数据库初始化完成")

# === Step 6: systemd 服务 ===
info("Step 6/7: 配置 systemd 服务...")
service_content = f'''[Unit]
Description=品牌沙盘 M1 FastAPI 服务
After=network.target mysql.service
Wants=mysql.service

[Service]
User=root
WorkingDirectory={APP_DIR}/backend
ExecStart={APP_DIR}/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port {APP_PORT} --workers 4
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
'''
Path("/etc/systemd/system/brand-sandtable.service").write_text(service_content)
run("systemctl daemon-reload")
run("systemctl enable brand-sandtable.service")
run("systemctl restart brand-sandtable.service")
info("systemd 服务已启动")

# === Step 7: Nginx + 防火墙 ===
info("Step 7/7: 配置 Nginx 反向代理...")
nginx_conf = '''server {
    listen 80;
    client_max_body_size 10M;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    root /opt/brand-sandtable/frontend;
    index visit_assistant_api.html index.html;

    location = / {
        try_files /visit_assistant_api.html =404;
    }

    location / {
        try_files $uri $uri/ =404;
    }
}
'''
Path("/etc/nginx/sites-available/brand-sandtable").write_text(nginx_conf)

# 启用站点
nginx_enabled = Path("/etc/nginx/sites-enabled")
if nginx_enabled.exists():
    Path("/etc/nginx/sites-enabled/brand-sandtable").symlink_to("/etc/nginx/sites-available/brand-sandtable")
    # 删除默认站点
    for f in nginx_enabled.glob("default*"):
        f.unlink()

run("nginx -t")
run("systemctl reload nginx")

# 防火墙
run("ufw allow 80/tcp", check=False)
run("ufw allow 443/tcp", check=False)
run("ufw allow 22/tcp", check=False)
run("ufw --force enable", check=False)
info("Nginx 配置完成")

# === 完成 ===
ip = subprocess.run("curl -s ifconfig.me", shell=True, capture_output=True, text=True).stdout.strip()
print(f"""
{GREEN}=============================================={NC}
{GREEN}  ✅ 品牌沙盘 M1 部署完成！{NC}
{GREEN}=============================================={NC}

访问地址:    http://{ip}
API 文档:    http://{ip}/docs

MySQL root 密码: {DB_ROOT_PASS}
MySQL app  密码: {DB_APP_PASS}
（已保存至 {APP_DIR}/backend/.env）

⚠️  请确认京东云安全组已开放 80 端口！
   控制台 → 轻量云主机 → 实例详情 → 防火墙 → 添加 TCP 80

服务管理:
  systemctl status brand-sandtable
  journalctl -u brand-sandtable -f
""")
