"""
品牌沙盘 M1 · 主工程 FastAPI 入口
只做应用组装：挂载各模块路由（routers/），业务逻辑写在各自 router 里。

启动: python3 main.py
文档: http://127.0.0.1:8000/docs

模块归属（见 docs/M1并行开发手册-正式版.md §六）:
- routers/profile.py 品牌档案 + 经营指标 + 完整度（佳璇，2026-06-11 合并）
- routers/brands.py  品牌 + 联系人 + 拜访前提醒（基底=培翛版，业务 owner=佳璇）
- routers/visits.py  拜访 / 记录 / 承诺 / 待办 / 健康度（培翛）
- routers/intel.py   情报：新闻/周报/预警/简报（开开，2026-06-11 合并）
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from config import SERVER_HOST, SERVER_PORT
from database import engine
from models import Base
from routers import brands, visits, profile, intel, auth, llm_api, dashboard, dw

# ---------- 建表（已存在则跳过） ----------
Base.metadata.create_all(bind=engine)

# ---------- FastAPI 实例 ----------
app = FastAPI(
    title="品牌沙盘 M1 · 主工程 API",
    version="1.0.0",
    description="品牌 / 拜访 / 情报 三模块统一后端（已全部接入：品牌档案 + 拜访 + 情报）",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- 挂载模块路由 ----------
# profile 必须先于 brands：/api/brands/profile/{x} 不能被 /api/brands/{name_key} 抢先匹配
app.include_router(auth.router)
app.include_router(llm_api.router)
app.include_router(dashboard.router)
app.include_router(dw.router)
app.include_router(profile.router)
app.include_router(brands.router)
app.include_router(visits.router)
app.include_router(intel.router)

# 组织架构图上传目录（profile org-image）
_uploads = Path(__file__).resolve().parent / "uploads"
_uploads.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_uploads)), name="uploads")


# ---------- 入口 ----------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=SERVER_HOST, port=SERVER_PORT, reload=True)
