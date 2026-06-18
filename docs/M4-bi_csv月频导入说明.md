# M4 · bi_csv 月频导入说明（佳璇 + Max）

> **口径**：`period_type=monthly` · `period_value=YYYY-MM`（例 `2026-05`）  
> **来源**：佳璇手动维护底表 → 导出 CSV → Max **`source=bi_csv`** 导入

---

## 一、佳璇侧（本 zip 已改）

| 文件 | 改动 |
|------|------|
| `docs/数仓字段口径-v1.md` | 月频定稿 |
| `data/dw/brand_metrics_monthly.csv` | bi_csv 列格式样例 |
| `frontend/profile.html` | 数据截至 YYYY-MM · 近12月 · 环比文案 |
| `backend/main.py` | API 读 `monthly` |
| `backend/seed.py` | 本地 seed 改为 12 个月（2025-06～2026-05） |

---

## 二、你导出 CSV 怎么写

**必填列**（每行一个品牌 × 一个月份）：

```csv
name_key,period_type,period_value,gmv,gmv_wow,gmv_yoy,...
midea,monthly,2026-05,487.00,-8.10,48200,-10.50,...
joyoung,monthly,2026-05,512.00,6.20,22800,8.00,...
```

规则：

1. **`period_type` 必须写 `monthly`**（不写则 dw_sync 默认 weekly，会读不到）  
2. **`period_value` 必须 `YYYY-MM`**，与底表一致，不要 `202606` / `2026M06`  
3. **`gmv` 单位万元**，与口径文档一致  
4. 历史月可分批导入（建议每次带近 12 月，供趋势图）  
5. 列名小写，与 `brand_metrics_monthly.csv` 对齐  

**从 Excel 导出注意**：UTF-8 CSV；数值不要带「万」字；空单元格可留空。

---

## 三、Max 侧必须改（否则 bi_csv 入库也看不到）

### 1. 档案 API（`server/routers/profile.py`）

把所有：

```python
BrandMetrics.period_type == "weekly"
```

改为：

```python
BrandMetrics.period_type == "monthly"
```

涉及：

- `GET /api/brands/profile/{name_key}`（最新指标）  
- `GET /api/brands/metrics/{name_key}`（近 N 条，注释改为「近 N 月」）  

可选更稳写法（Max 定夺）：

```python
.order_by(BrandMetrics.period_value.desc())  # YYYY-MM 字符串排序正确
.filter(BrandMetrics.brand_id == brand.id, BrandMetrics.period_type == "monthly")
```

### 2. bi_csv 导入

- `dw_sync.py` **已支持** `period_type=monthly`，**无需改导入逻辑**  
- 导入时指定 `source=bi_csv`（M4-C / D-M-M4-5）  
- CLI 示例（Max 环境）：

```bash
python3 run_dw_sync.py ../data/dw/bi_export_2026-05.csv --source bi_csv
```

### 3. 其他模块（联调）

| 模块 | 文件/位置 | 改什么 |
|------|-----------|--------|
| 拜访 | 培翛 | 「经营数据已更新至 **2026-05**」 |
| 情报 | `intel.py` | `_week_label` 等 Wxx 逻辑需兼容 `YYYY-MM` |
| 手册 | M4 附录 E | 示例从 `2026W24` 改为 `2026-05` |
| Seed/演示 | 生产库 | 勿再写 weekly 种子覆盖 monthly 真数 |

### 4. 质量规则（M4-C）

- `gmv_wow` 语义按 **月环比** 理解  
- `period_value` 校验建议：`^\d{4}-\d{2}$`  

---

## 四、验收步骤（D-J-M4-1）

1. Max 导入你的 `bi_csv` 批次成功（`dw_import_batch.status=success`）  
2. 打开外网档案 → 顶栏 **数据截至 2026-05**  
3. 五品牌（或至少 1 品牌）GMV 与底表 Excel **逐格对照** → 截图填口径 §4  
4. 换品牌 KPI / 趋势图随 `period_value` 变化  

---

## 五、发群模板

```text
【档案】【M4 口径变更】品牌销售/市占改为月更底表，
bi_csv 导入：period_type=monthly，period_value=YYYY-MM（例 2026-05）。
请 Max M4-C：profile/metrics API 改读 monthly；
D-J-M4-1 验收改为月度 GMV 对照。
佳璇 zip 已含月频 UI + 口径文档 + brand_metrics_monthly.csv 样例。
```
