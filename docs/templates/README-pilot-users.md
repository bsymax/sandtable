# 采销试点名单（M6）· 存放与更新约定

## 文件分工

| 路径 | 用途 | 能否导入 |
|------|------|----------|
| `pilot-users-m6.example.csv` | **格式样例**（虚构 username，给开开/AI 对照列名） | ❌ 禁止 |
| **`pilot-users-m6.csv`** | **正式名单**（开开清洗后交 Max，仓库内唯一导入源） | ✅ |
| `archive/pilot-users-m6-*.csv` | **历史快照**（每次换版前归档，便于 diff / 回滚对照） | ❌ 仅存档 |

> CSV **禁止**含 `password` 列。统一初始密码由 Max 导入时通过 `--preset-password` 传入，**不得写入 git**。

---

## 开开交新版本时（Max 操作）

1. 收到文件（如 `pilot-users-m6-0701.csv`）→ 先复制到  
   `docs/templates/archive/pilot-users-m6-MMDD.csv`
2. 覆盖主文件：`docs/templates/pilot-users-m6.csv`
3. 本机或 117 **dry-run** 校验：

   ```bash
   cd server && python3 ../scripts/import-pilot-users.py \
     ../docs/templates/pilot-users-m6.csv --dry-run --strict
   ```

4. 117 正式导入（须已部署 M6-A 十一品牌）：

   ```bash
   M6_PRESET_PASSWORD='（统一密码，勿写入脚本）' \
     bash deploy/point-deploy-m6-b-import.sh --apply
   ```

5. 更新手册 `M6并行开发手册-正式版.md` 附录 H.0 快照说明 · 开开发群公告

---

## 117 上运行时文件

导入脚本会把 CSV 拷到 **`/opt/sandtable/data/pilot-users-m6.csv`** 再执行；  
**以 git 仓库 `docs/templates/pilot-users-m6.csv` 为准**，117 上是部署副本。

---

## brand_keys 说明

- 名单里可写 **legacy 占位**（`jc_a`～`jc_e`、`faenza`、`annwa` 等），导入时经 `data/brands_master.json` 的 `legacy_name_key_map` 映射为库内真名。
- 新增第 11 品牌 `carpoly` 后，若需绑定用户，在 CSV 的 `brand_keys` 中加 `carpoly` 或 `jc_f`（二者等价）。

---

*当前正式版：archive/pilot-users-m6-0701.csv · 39 人（2026-07-01 开开交付）*
