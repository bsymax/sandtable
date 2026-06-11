# 品牌沙盘 M1 · 品牌情报平台（情报席）

> 交付人：开开 | 交付日期：2026-06-11 | 阶段：S1+S2 完整包
> 技术栈：FastAPI + SQLAlchemy + MySQL + 原生 HTML/CSS/JS

## 启动三步曲

### 1. 建库

确保 MySQL 中已有 `brand_sandtable` 库和 brands/visits 等公共表（来自培翛拜访模块），然后导入情报表：

```bash
mysql -u root -p --default-character-set=utf8mb4 < database/schema.sql
```

### 2. 配置

编辑 `backend/.env`，修改数据库密码：

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的密码
DB_NAME=brand_sandtable
```

### 3. 安装依赖 & 启动

```bash
cd backend
pip3 install -r requirements.txt
python3 main.py
```

服务启动在 `http://127.0.0.1:8002`，API 文档 `http://127.0.0.1:8002/docs`。

### 4. 打开前端

浏览器打开 `frontend/intelligence.html`。

---

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/brands` | 品牌下拉列表（公共） |
| GET | `/api/intel/news` | 新闻列表（支持 brand_id/sentiment/category 筛选） |
| POST | `/api/intel/news` | 录入新闻（URL 自动去重） |
| GET | `/api/intel/news/{id}` | 新闻详情 |
| POST | `/api/intel/alerts` | 录入情报预警 |
| GET | `/api/intel/alerts` | 预警列表（支持 brand_id/priority/status 筛选） |
| PUT | `/api/intel/alerts/{id}` | 更新预警状态 |
| POST | `/api/intel/alerts/{id}/create-visit` | 从预警一键创建紧急拜访 |
| POST | `/api/intel/weekly` | 提交周报 |
| GET | `/api/intel/weekly` | 周报列表 |
| GET | `/api/intel/weekly/latest` | 各品牌最新周报 |
| GET | `/api/intel/weekly-summary` | 规则版周报摘要 |
| GET | `/api/intel/briefing/{brand_key}` | 品牌情报简报（新闻+预警+周报） |
| GET | `/api/intel/stats` | 情报总览统计 |

完整 Swagger 文档：`http://127.0.0.1:8002/docs`

---

## 数据库表

| 表名 | 说明 |
|------|------|
| intel_news | 外部新闻资讯（品牌/标题/摘要/来源/情感/分类/去重） |
| intel_alerts | 情报预警（P0-P3/描述/建议/状态/关联拜访） |
| intel_weekly_reports | 内部周报（GMV/竞品/库存/风险/机会/计划） |
| intel_briefing_cache | 简报缓存（品牌维度） |

所有表使用 snake_case，均包含 `created_at` / `updated_at`。

---

## 前端功能

1. **情报预警列表** — P0 红色脉冲标记，品牌/级别/状态筛选，关键词搜索
2. **新闻列表** — 按情感分类着色（负面红/正面绿/中性蓝），展示来源/分类/时间
3. **录入表单** — 情报预警录入、新闻录入、周报提交（含默认本周日期）
4. **周报摘要（规则版）** — 模板拼接：「本周新增情报 N 条（P0×a/P1×b），主要涉及{品牌}，最高优先级：{标题}」
5. **一键拜访** — 从预警直接创建紧急拜访（POST 到 visits 表）
6. **品牌情报简报** — 按品牌聚合新闻+预警+周报

---

## 已知问题 / 未做

- 外部新闻自动抓取（M2 接入新闻 API）
- LLM 智能摘要（M2 接入大模型）
- 企微/邮件推送通知（M2）
