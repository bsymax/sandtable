#!/usr/bin/env bash
# 构建 M1 联调 baseline 包 + 只读对照包，输出到 deliverables/*.zip
# 用法：在项目根目录执行  bash scripts/build-m1-baseline-packages.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/deliverables"
STAMP="$(date +%Y%m%d)"

rm -rf "$OUT"
mkdir -p "$OUT"

echo "==> 构建目录: $OUT"

copy_common_docs() {
  local dest="$1"
  mkdir -p "$dest/docs"
  cp "$ROOT/docs/M1联调基准说明.md" "$dest/docs/"
  cp "$ROOT/docs/发给模块席-开包说明.md" "$dest/docs/"
}

# ---------- 佳璇 ----------
JIA="$OUT/jiaxuan-m1-0612-baseline"
echo "==> 佳璇 baseline"
rsync -a --exclude '.env' --exclude '__pycache__' --exclude '*.pyc' \
  "$ROOT/jiaxuan-m1-0610/" "$JIA/"
mkdir -p "$JIA/synced-from-main/server/routers" "$JIA/frontend/js"
cp "$ROOT/server/routers/profile.py" "$JIA/synced-from-main/server/routers/"
cp "$ROOT/server/completeness.py" "$JIA/synced-from-main/server/"
cp "$ROOT/web/profile.html" "$JIA/frontend/profile.html"
cp "$ROOT/web/js/shell.js" "$JIA/frontend/js/"
copy_common_docs "$JIA"

cat > "$JIA/README-BASELINE.md" <<'EOF'
# 佳璇 · M1 联调基准包（0612-baseline）

> 在 `jiaxuan-m1-0610` 基础上，已从 Max 主工程同步联调通过版前端与 API 参考代码。

## 与 0610 包的主要差异

| 项 | 0610 | 本 baseline |
|----|------|-------------|
| 档案页 | `brand_profile_api.html`，Tab3/4 演示数据 | **`frontend/profile.html`** = 主工程版，Tab3/4 真 API |
| 后端参考 | 仅 `backend/main.py` | 增加 **`synced-from-main/server/routers/profile.py`**（与主工程一致） |
| 侧栏 | 无 | **`frontend/js/shell.js`**（合并版统一壳） |

## M2 开发指引

1. **UI**：改 `frontend/profile.html`（或从 `synced-from-main` 对照）
2. **API**：改 `backend/` 内档案相关代码，并与 `synced-from-main/server/routers/profile.py` 保持路径一致
3. **表**：只动 `brand_profiles`、`brand_metrics`；schema 见 `database/schema.sql`（勿全量 DROP 公共表）
4. 完成后 zip 本文件夹发给 Max

## 快速启动（单模块，端口 8001）

见原 `README.md`。要看 Tab3/4 真效果，需 Max 主工程三服务（8000+5510）或等外网地址。

## 必读

`docs/M1联调基准说明.md` §3.2、§七（佳璇自查项）
EOF

# 档案相关表 SQL 片段
mkdir -p "$JIA/database"
awk '/brand_profiles|brand_metrics/{p=1} p{print} /^-- [0-9]+\./ && !/brand_profiles|brand_metrics/{if(seen)exit} /CREATE TABLE brand_profiles/{seen=1}' \
  "$ROOT/database/schema.sql" > "$JIA/database/schema-profile-tables-snippet.sql" 2>/dev/null || \
  echo "-- 完整 schema 见主工程 database/schema.sql 中 brand_profiles / brand_metrics 段" \
  > "$JIA/database/schema-profile-tables-snippet.sql"

# ---------- 开开 ----------
KAI="$OUT/kaikai-m1-0612-baseline"
echo "==> 开开 baseline"
rsync -a --exclude '.env' --exclude '__pycache__' --exclude '*.pyc' \
  "$ROOT/kaikai-m1-0611/" "$KAI/"
mkdir -p "$KAI/synced-from-main/server/routers" "$KAI/synced-from-main/database" "$KAI/frontend/js"
cp "$ROOT/server/routers/intel.py" "$KAI/synced-from-main/server/routers/"
cp "$ROOT/database/migrate_intel_unify.sql" "$KAI/synced-from-main/database/"
cp "$ROOT/web/intel.html" "$KAI/frontend/intel.html"
cp "$ROOT/web/js/shell.js" "$KAI/frontend/js/"
copy_common_docs "$KAI"

cat > "$KAI/README-BASELINE.md" <<'EOF'
# 开开 · M1 联调基准包（0612-baseline）

> ⚠️ **Breaking change**：周报不再使用 `intel_weekly_reports`，已并入 **`brand_metrics`**。

## 与 0611 包的主要差异

| 项 | 0611 | 本 baseline |
|----|------|-------------|
| 周报底表 | `intel_weekly_reports` | **`brand_metrics` 扩展列**（见 migrate 脚本） |
| 预警 | 无 category | **`category`**：增长机会 / 风险预警 |
| 前端 | `intelligence.html` | **`frontend/intel.html`**：整页 `?brand=` 筛选 + 编辑 |
| 后端 | `backend/main.py` 旧模型 | **`synced-from-main/server/routers/intel.py`** 为准 |

## M2 开发指引

1. **必读** `docs/M1联调基准说明.md` **§3.3**
2. 后端以 `synced-from-main/server/routers/intel.py` 为模板；勿再扩展 `IntelWeeklyReport`
3. 已有库升级：执行 `synced-from-main/database/migrate_intel_unify.sql`
4. 新库：用主工程 `database/schema.sql` 情报段（无 intel_weekly_reports）
5. 完成后 zip 发给 Max

## 快速启动（单模块，端口 8002）

见原 `README.md`。**注意**：0611 的 `backend/main.py` 与主工程已不一致，联调级自测请对照 `synced-from-main` 或等 Max 外网环境。

## 自查

`docs/M1联调基准说明.md` §七（开开项）
EOF

cp "$ROOT/database/migrate_intel_unify.sql" "$KAI/database/migrate_intel_unify.sql"

cat > "$KAI/database/README-情报表变更.md" <<'EOF'
# 情报表变更（0612 联调）

- 废弃：`intel_weekly_reports`
- 周报叙事字段：写入 `brand_metrics`（week_start, competitor_moves, intel_report_status 等）
- 预警：`intel_alerts.metrics_id` → `brand_metrics.id`；新增 `category`
- 迁移：`synced-from-main/database/migrate_intel_unify.sql` 或主工程 `database/migrate_intel_unify.sql`
EOF

# ---------- 培翛 ----------
PEI="$OUT/peixiao-m1-0612-baseline"
echo "==> 培翛 baseline"
if [[ -d "$ROOT/peixiao-m1-0612" ]]; then
  SRC_PEI="$ROOT/peixiao-m1-0612"
else
  SRC_PEI="$ROOT/peixiao-m1-0610"
fi
rsync -a --exclude '.env' --exclude '__pycache__' --exclude '*.pyc' \
  "$SRC_PEI/" "$PEI/"
mkdir -p "$PEI/synced-from-main/server/routers" "$PEI/frontend/js"
cp "$ROOT/server/routers/visits.py" "$PEI/synced-from-main/server/routers/"
cp "$ROOT/server/routers/brands.py" "$PEI/synced-from-main/server/routers/"
cp "$ROOT/web/visit.html" "$PEI/frontend/visit.html"
cp "$ROOT/web/js/visit-common.js" "$PEI/frontend/js/"
cp "$ROOT/web/js/shell.js" "$PEI/frontend/js/"
copy_common_docs "$PEI"

cat > "$PEI/README-BASELINE.md" <<'EOF'
# 培翛 · M1 联调基准包（0612-baseline）

> S2（承诺改状态 + 按行拆条）及 visit 页三处独立品牌筛选，已在主工程验收通过。

## 与 0612 交付包的主要差异

| 项 | 原 peixiao 包 | 本 baseline |
|----|---------------|-------------|
| S2 承诺 | 包内可能缺失 | **`synced-from-main/server/routers/visits.py`** 已含 |
| 前端 | `visit_assistant_api.html` | **`frontend/visit.html`** + **`js/visit-common.js`** |
| 品牌筛选 | 跟安排拜访联动 | 记录/承诺/日历 **各自独立筛选**，默认全部品牌 |

## M2 开发指引

1. 改 `frontend/visit.html` 与 `synced-from-main/server/routers/visits.py`
2. 公共表 `brands` 只读；拜访 7 张表归培翛 owner
3. 跨模块链接用 `visit.html`（勿用 visit_assistant_api.html）
4. 完成后 zip 发给 Max

## 快速启动

见原 `README.md`（端口 8000）。合并版页面请用 `frontend/visit.html` + 主工程 5510 静态服务查看。

## 自查

`docs/M1联调基准说明.md` §3.4、§七（培翛项）
EOF

# ---------- 只读对照包 ----------
REF="$OUT/sandtable-m1-reference-readonly"
echo "==> 只读对照包"
mkdir -p "$REF"
for item in server web database docs seed index.html sandtableM1.html scripts; do
  if [[ -e "$ROOT/$item" ]]; then
    rsync -a --exclude '.env' --exclude '__pycache__' --exclude '*.pyc' \
      "$ROOT/$item" "$REF/"
  fi
done
cp "$ROOT/docs/M1联调基准说明.md" "$REF/docs/" 2>/dev/null || true
cp "$ROOT/docs/发给模块席-开包说明.md" "$REF/docs/" 2>/dev/null || true

cat > "$REF/README-只读对照.md" <<'EOF'
# sandtable M1 · 只读对照包

**不要在本目录开发 M2。** 仅供对照 Max 主工程联调通过后的完整效果。

## 启动（与 Max 本机一致）

见 `docs/M1联调基准说明.md` 或主手册附录 C：

1. MySQL 3306
2. `cd server && python3 -m uvicorn main:app --host 127.0.0.1 --port 8000`
3. 项目根 `python3 -m http.server 5510 --bind 127.0.0.1`
4. 打开 http://127.0.0.1:5510/web/index.html

## 不含

- `.env`（请复制 `server/.env.example` 自行配置）
- 各模块旧交付包目录（`*-m1-0610` 等）
- git 历史

## M2 开发

请使用各自 `xxx-m1-0612-baseline.zip` 交付包。
EOF

# ---------- 打 zip ----------
echo "==> 打包 zip"
cd "$OUT"
for dir in jiaxuan-m1-0612-baseline kaikai-m1-0612-baseline peixiao-m1-0612-baseline sandtable-m1-reference-readonly; do
  zip -r -q "${dir}.zip" "$dir"
  echo "    ${dir}.zip  ($(du -h "${dir}.zip" | cut -f1))"
done

# 汇总清单
cat > "$OUT/清单.txt" <<EOF
M1 联调基准包 · 生成时间 ${STAMP}
路径: ${OUT}

发给佳璇: jiaxuan-m1-0612-baseline.zip
发给开开: kaikai-m1-0612-baseline.zip
发给培翛: peixiao-m1-0612-baseline.zip
全员对照: sandtable-m1-reference-readonly.zip

说明文档（也在各 zip 内）:
- docs/M1联调基准说明.md
- docs/发给模块席-开包说明.md

群消息模板见 docs/发给模块席-开包说明.md
EOF

echo ""
echo "✅ 完成。输出目录: $OUT"
ls -lh "$OUT"/*.zip
