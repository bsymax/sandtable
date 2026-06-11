# 品牌档案交付包 · 与 sandtableM1 Demo 对齐说明

> 交付包：`jiaxuan-m1-0610` · 佳璇 · 品牌席 · S0～S3

## 已对齐（真数据 · MySQL API）

| 区块 | 说明 |
|------|------|
| 5 品牌 Tab | 切换拉取 `GET /api/brands/profile/{name_key}` |
| 经营看板 | 6 KPI 单行、P0 缺口面板、4 张 Chart.js 图、类目维度市占表、TOP20 对标折叠面板 |
| 品牌简介 | 基础信息、关键人物可编辑、组织架构简图（含连接线）、潜规则可编辑写库 |
| 档案完整度 | 10 分制圆环 + API 字段 |
| 顶部 AI 一行摘要 | 按品牌静态文案（与 Demo 一致，S5 可接 LLM） |

## 演示预览（S4 由 Max 聚合真 API）

| 区块 | 当前 | S4 后 |
|------|------|-------|
| 📡 最新情报 | sandtableM1 样例 TOP3 机会/风险 | 开开 `GET /api/intel` |
| 🤝 历史互动 | 样例时间轴 + 承诺追踪 + AI 拜访建议 | 培翛拜访/承诺 API |
| P0 缺口 SKU 明细 | 样例 SKU 列表（与 Demo 一致） | 供给库 / BI 对接 |
| 安排拜访 / 情报库 按钮 | Toast 提示 | 跨模块跳转 |

## 与完整沙盘 Demo 的已知差异（可接受）

- 无左侧全局导航（工作台/情报流/拜访助手）— 本包为**独立模块交付**
- 无跨模块 `switchModule()` — S4 合并进主工程后由 Max 接线
- 圆环标签为「完整度」非 Demo「健康分」（业务语义更准确）

## 验收命令

```bash
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8001/api/brands/profile/midea
curl "http://127.0.0.1:8001/api/brands/metrics/midea?limit=12"
```

浏览器：`http://127.0.0.1:8001/`
