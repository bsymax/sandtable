"""
品牌沙盘 M1 · 主工程 FastAPI 入口
只做应用组装：挂载各模块路由（routers/），业务逻辑写在各自 router 里。

启动: python3 main.py
文档: http://127.0.0.1:8000/docs

模块归属（见 docs/M1并行开发手册-正式版.md §六）:
- routers/brands.py  品牌 + 联系人 + 拜访前提醒（基底=培翛版，业务 owner=佳璇）
- routers/visits.py  拜访 / 记录 / 承诺 / 待办 / 健康度（培翛）
- routers/intel.py   情报（开开，S4 合并时加入）
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import SERVER_HOST, SERVER_PORT
from database import engine
from models import Base
from routers import brands, visits

# ---------- 建表（已存在则跳过） ----------
Base.metadata.create_all(bind=engine)

# ---------- FastAPI 实例 ----------
app = FastAPI(
    title="品牌沙盘 M1 · 主工程 API",
    version="1.0.0",
    description="品牌 / 拜访 / 情报 三模块统一后端（当前已接入：拜访 + 品牌基底）",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- 挂载模块路由 ----------
app.include_router(brands.router)
app.include_router(visits.router)
# app.include_router(intel.router)   # S4 合并开开的情报模块时取消注释


# ---------- 入口 ----------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=SERVER_HOST, port=SERVER_PORT, reload=True)
