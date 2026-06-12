# 生产快照 · 117.72.211.51 · 2026-06-13-2

**Git tag**: `prod-web-2026-06-13-2`（区别于 `prod-web-2026-06-13`）

## 变更摘要

- S5 工作台：index 瘦身 + 全 API 聚合（待办/承诺/情报/健康度）
- 新增 `web/js/api-base.js`：本机 5510→8000，生产走同源
- 三模块页 profile/visit/intel 统一 API 根地址
- 后端：`TodoOut` 含 `brand_name`；`GET/PUT /api/todos` 返回品牌

## 部署

```bash
bash deploy/point-deploy-prod-web-2026-06-13-2.sh 117.72.211.51
```

## 回滚

| 目标 | 命令 |
|------|------|
| 回到 **本快照** | `bash deploy/snapshots/prod-117.72.211.51-2026-06-13-2/rollback-web.sh` |
| 回到 **上一版** `prod-web-2026-06-13` | `bash deploy/snapshots/prod-117.72.211.51-2026-06-13/rollback-web.sh` |
