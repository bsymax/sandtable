# 发给 Max · M6 佳璇终包合并说明

> **交付人**：陈佳璇 · 品牌席 · 档案 + 数仓 + 谈参  
> **包名**：`jiaxuan-m6-trial.zip`  
> **日期**：2026-06-10 · **对照**：§3.4 D-J-M6

---

## 1. 本包一句话

十一品牌主数据 + 档案页全量增强 + 建材 6 品牌数仓真数 + **完整度 12 分（含情报/互动）** + **谈参工具包（PDF）**。

---

## 2. Max 必做（合并前）

| # | 事项 | 说明 |
|---|------|------|
| **M-1** | **扩品牌槽 id=11** | `name_key=carpoly` · 中文「嘉宝莉」· 占位 `jc_f` |
| **M-2** | **合并 profile 路由** | 以 `synced-from-main/server/routers/profile.py` 为准，叠加 org 图片、简介字段、完整度 12 分逻辑 |
| **M-3** | **合并 completeness.py** | `server/completeness.py` ← 本包 `synced-from-main/server/completeness.py` |
| **M-4** | **静态页** | `web/profile.html` ← `frontend/profile.html` |
| **M-5** | **谈参** | `web/toolkit/talking-points.html` ← 本包（**覆盖培翛占位，以佳璇版为准**） |
| **M-6** | **shell.js** | 合并 `toolkit/talking-points.html` 的 `MODULE_PAGES` 条目；副标题「建材业务部」 |
| **M-7** | **数仓 seed** | 导入 `data/dw/brand_metrics_monthly.csv` · `brand_category_monthly.csv`（含 6 建材） |
| **M-8** | **依赖** | `python-multipart`（组织图上传）已在 `requirements.txt` |

情报/拜访完整度加分依赖主工程已有表 `intel_alerts` · `intel_news` · `visits`；佳璇 standalone SQLite 无表时该项为 0，合并 MySQL 后自动生效。

---

## 3. 文件映射（baseline → 主工程）

| 本包路径 | 建议主工程路径 |
|----------|----------------|
| `frontend/profile.html` | `web/profile.html` |
| `frontend/toolkit/talking-points.html` | `web/toolkit/talking-points.html` |
| `frontend/toolkit/brand-report.html` | `web/toolkit/brand-report.html` |
| `frontend/js/shell.js` | `web/js/shell.js`（**按需 cherry-pick**，避免覆盖培翛 visit 改动） |
| `synced-from-main/server/routers/profile.py` | `server/routers/profile.py` |
| `synced-from-main/server/completeness.py` | `server/completeness.py` |
| `backend/org_structure.py` | `server/org_structure.py`（**新文件**，profile 路由需 import） |
| `backend/schemas.py` | 合并 `BrandProfileUpdate` / `OrgImageOut` 等增量字段 |
| `backend/models.py` | `role_tag` VARCHAR(32) 等 |
| `data/brands_master.json` | `data/brands_master.json` |
| `data/dw/*` | `data/dw/*` |
| `backend/seed.py` | 参考更新 seed / migrate 脚本 |

**本地 standalone API**（仅开发用）：`backend/main.py` 含 org-image、toolkit 静态挂载；合并时把对应 endpoint 并入主 `main.py` 或 profile router。

---

## 4. 功能改动明细（供 Code Review）

### 4.1 品牌档案 `profile.html`

- 十一品牌 Tab（5 卫浴 + 6 建材）
- 建材三级类目市占表 + 布局机会（与卫浴二级口径一致，颗粒度不同）
- 竞争格局 / 增长机会：空则规则保底文案；用户保存后不覆盖
- 可编辑：简介、组织架构（分支/岗位）、组织图图片、关键人物、潜规则、竞争/机会
- 完整度圆环 **x/12**

### 4.2 数仓

- 卫浴：`transform_brand_source.py` · `transform_category_source.py`
- 建材：`transform_jc_brand_source.py` · `transform_jc_category_source.py`
- CSV 已含 **carpoly** 2025-05～2026-05 月度数据
- 口径：JD 渠道 GMV/销量；四渠道市占/增速 — 见 `docs/数仓字段口径-v1.md`

### 4.3 完整度 `completeness.py`

新增函数：`count_brand_intel()` · `count_brand_interactions()`  
`calc_completeness(..., intel_count=, interaction_count=)` · `max_score=12`

### 4.4 谈参 `talking-points.html`

- 流程：选品牌 → 6 模块编辑 → 预览 → PDF
- 自动导入：档案 API `profile` + `metrics?limit=24`，生成 2026 YTD 经营叙述（**无分月成交列表**）
- 主题色 `#8B0000` + 白；PDF 用 cdn html2pdf.js
- API：`GET /api/brands` · `/api/brands/profile/{key}` · `/api/brands/metrics/{key}`

---

## 5. 与培翛包的关系

- 手册 V1.2 原分工：谈参归培翛；**主工程未落地 toolkit 页面**
- **本终包由佳璇交付谈参**，请 Max **以本包 `talking-points.html` 为准**
- 培翛 `visit.html` 内品牌报告 Tab **本包未改**；侧栏「品牌报告」跳转本包 `brand-report.html` → 谈参

---

## 6. 合并后验收（117 / §3.4）

| # | 检查项 |
|---|--------|
| 1 | 11 品牌档案可开，carpoly 有 KPI |
| 2 | 完整度显示 `/12`，有情报/拜访的品牌多 1～2 分 |
| 3 | `/toolkit/talking-points.html` 选九牧 → 模块 1 有 2026 数据 → PDF 可下 |
| 4 | org 图片上传保存后刷新仍在 |
| 5 | 只读账号 FAQ 行为不变 |

---

## 7. 群聊模板（佳璇 → Max）

```text
@Max 佳璇 M6 终包 jiaxuan-m6-trial.zip 已发。

请合并：
① id=11 carpoly/jc_f 扩槽
② profile + completeness 12 分（情报+互动）
③ 建材 6 品牌数仓 CSV + 档案页
④ 谈参 toolkit/talking-points.html（PDF，经营数据联动档案）

详细映射与冲突说明见包内 docs/发给Max-M6佳璇终包说明.md、PATCHLOG.md。
本地已验 8010，问题随时 @我。
```

---

## 8. 已知限制 / 后续

| 项 | 说明 |
|----|------|
| 建材 6 品牌 responsible | seed 仍为「待定」，待业务提供采销姓名 |
| 深度指标 gross_margin 等 | 建材 CSV 暂无，完整度第 10 项可能不满 |
| 谈参 PDF | **已本地化** `web/js/html2pdf.bundle.min.js`（jiaxuan-m6-0702 · 不依赖 CDN） |
| Tab3/4 情报拜访 | 仍依赖开开模块 API（8000 主工程） |
