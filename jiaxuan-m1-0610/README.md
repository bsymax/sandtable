# 品牌沙盘 M1 · 品牌档案模块

佳璇交付包 · S1～S3（数据层 + 编辑 + Chart.js 图表 + 档案完整度）

## 项目结构

```
jiaxuan-m1-0610/
├── backend/              # FastAPI（端口 8001）
│   ├── main.py schemas.py models.py database.py config.py
│   ├── completeness.py seed.py requirements.txt
│   └── .env.example      # 复制为 .env 后改密码
├── frontend/
│   └── brand_profile_api.html
├── database/schema.sql
├── .vscode/              # F5 启动调试
├── DEMO对齐说明.md       # 与 sandtableM1 差异清单
└── README.md
```

## 快速启动

### 1. 确保 Docker MySQL 在跑

```bash
/Applications/Docker.app/Contents/Resources/bin/docker ps
# 应看到 sandtable-mysql Up
```

### 2. 建库（首次或需要重建时）

在 `jiaxuan-m1-0610` 目录下：

```bash
# 全量建库（会重建所有表）
docker exec -i sandtable-mysql mysql -uroot -p'Sandtable@2026' --default-character-set=utf8mb4 < database/schema.sql
```

若已有培翛数据，只需追加佳璇两张表，在 `backend` 目录执行：

```bash
python3 seed.py   # 自动建表 + 导入种子数据（表为空时）
```

### 3. 配置环境变量（首次）

```bash
cd backend
cp .env.example .env
# 按需修改 DB_PASSWORD 等
```

### 4. 安装依赖 & 启动后端

```bash
cd backend
pip3 install -r requirements.txt
python3 main.py
```

服务地址：`http://127.0.0.1:8001`  
API 文档：`http://127.0.0.1:8001/docs`

## 打开前端

**推荐**：后端启动后，浏览器地址栏输入：

```
http://127.0.0.1:8001/
```

也可直接双击打开 `frontend/brand_profile_api.html`（需后端 8001 在跑）。

功能：5 品牌 Tab · 4 子 Tab（经营看板/品牌简介/最新情报/历史互动）· 经营看板 4 张 Chart.js 图 + P0 缺口明细 · 品牌简介可编辑 · 档案完整度圆环 + AI 摘要。

> **与 sandtableM1 的差异**：经营看板 + 品牌简介 = **真数据（MySQL API）**；最新情报 + 历史互动 = **演示预览（样例数据）**，S4 由 Max 对接开开情报库 + 培翛拜访 API 后切换真数据。

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/brands/profile/{name_key}` | 品牌档案（含 completeness_score/percent） |
| GET | `/api/brands/metrics/{name_key}?limit=12` | 近 N 周经营指标（倒序） |
| PUT | `/api/brands/profile/{name_key}` | 更新潜规则 / 关键联系人 |
| GET | `/health` | 健康检查 |

`name_key` 取值：`midea` / `joyoung` / `supor` / `bear` / `morphy`

### 验证示例

```bash
curl http://127.0.0.1:8001/api/brands/profile/midea
curl "http://127.0.0.1:8001/api/brands/metrics/midea?limit=12"
```

profile 响应含 `completeness_score`（10 分制）、`completeness_percent`；metrics 返回 12 条周度记录。

## S3 回归记录

| 检查项 | 结果 |
|--------|------|
| 五品牌 metrics API 各 12 条 | ✅ curl 通过 |
| 档案完整度字段 | ✅ midea 10/100%，morphy 8/80%（taboos 待补全扣 1 分） |
| 后端启动 + seed 补 12 周 | ✅ `python3 seed.py` |
| 浏览器全量回归（五品牌 Tab + 图表 + 编辑 + F12） | ✅ 佳璇自测通过 |
| 前端访问地址 | ✅ `http://127.0.0.1:8001/` |

## 数据库表

| 表名 | 说明 | Owner |
|------|------|-------|
| brands | 品牌主数据（公共，只读） | 培翛基准 |
| brand_contacts | 品牌联系人（公共，只读） | 培翛基准 |
| brand_profiles | 品牌简介/潜规则 | 佳璇 |
| brand_metrics | 经营指标快照 | 佳璇 |

## 已知问题 / 未完成

- [x] S2：前端编辑保存
- [x] S3：多周指标 API + Chart.js + 档案完整度
- [ ] S4：最新情报 / 历史互动 Tab（Max 聚合）

## 技术栈

Python 3.10+ / FastAPI / SQLAlchemy / MySQL 8 / 原生 HTML+CSS+JS
