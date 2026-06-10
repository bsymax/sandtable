# 品牌沙盘 M1 · 智能拜访助手

企业级品牌拜访管理工具，覆盖 **安排拜访 → 拜访记录 → 承诺跟踪 → 待办生成 → 健康度分析** 全链路。

## 项目结构

```
brand-sandtable-m1/
├── backend/                  # FastAPI 后端
│   ├── main.py               # 主应用 & API 路由
│   ├── models.py             # SQLAlchemy ORM 模型
│   ├── schemas.py            # Pydantic 请求/响应模型
│   ├── config.py             # 环境变量配置
│   ├── database.py           # 数据库会话管理
│   ├── requirements.txt      # Python 依赖
│   └── .env                  # 数据库连接（需配置密码）
├── frontend/                 # 前端页面
│   ├── visit_assistant_api.html  # [主要] 对接 API 的拜访助手
│   ├── visit_assistant.html      # 纯静态演示版
│   ├── index.html                # 企业 AI 平台首页
│   └── api.js                    # API 封装库（独立引用）
├── database/
│   └── schema.sql            # 建表脚本 + 种子数据
├── .vscode/
│   ├── settings.json         # VS Code 推荐配置
│   └── launch.json           # 调试启动配置
└── .gitignore
```

## 快速启动

### 1. 创建数据库

```bash
mysql -u root -p < database/schema.sql
```

> 注（Max 2026-06-10 合并时修订）：schema.sql 已加 `SET NAMES utf8mb4`（防中文乱码）与 `SET FOREIGN_KEY_CHECKS=0`（支持重复执行），可放心反复导入。

### 2. 配置后端

编辑 `backend/.env`，修改数据库密码：

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的密码
DB_NAME=brand_sandtable
```

### 3. 安装依赖 & 启动后端

```bash
cd backend
pip install -r requirements.txt --break-system-packages
python main.py
```

服务启动在 `http://127.0.0.1:8000`，自动生成 API 文档在 `http://127.0.0.1:8000/docs`。

### 4. 打开前端

用 VS Code Live Server 或直接浏览器打开 `frontend/visit_assistant_api.html`。

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/brands` | 品牌下拉列表 |
| GET | `/api/brands/{key}` | 品牌详情 |
| GET | `/api/brands/{key}/reminder` | 拜访前提醒 |
| POST | `/api/visits` | 安排拜访 |
| GET | `/api/visits` | 拜访列表（支持筛选） |
| PUT | `/api/visits/{id}` | 更新拜访状态 |
| DELETE | `/api/visits/{id}` | 删除拜访 |
| POST | `/api/records` | 保存记录 + 自动生成待办 |
| GET | `/api/records` | 近期记录 |
| PUT | `/api/commitments/{id}` | 更新承诺状态 |
| GET | `/api/todos` | 待办列表 |
| PUT | `/api/todos/{id}` | 更新待办 |
| GET | `/api/health` | 拜访频率健康度 |

完整 Swagger 文档：`http://127.0.0.1:8000/docs`

## 数据库表

| 表名 | 说明 |
|------|------|
| brands | 品牌主数据（美的/九阳/苏泊尔/小熊/摩飞） |
| brand_contacts | 品牌联系人 |
| visits | 拜访安排 |
| visit_attendees | 拜访参与人员 |
| visit_records | 拜访后记录 |
| commitments | 承诺事项 |
| todos | 待办事项 |

## 技术栈

- **后端**: Python 3.10+ / FastAPI / SQLAlchemy / PyMySQL
- **数据库**: MySQL 8.0+
- **前端**: 原生 HTML/CSS/JS（零框架依赖）
