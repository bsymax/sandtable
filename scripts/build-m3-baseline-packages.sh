#!/usr/bin/env bash
# M3 开工 baseline 包 · 从主工程 + M2 包结构生成
# 用法：bash scripts/build-m3-baseline-packages.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/deliverables"
RECV="$OUT/received"
CODE="0622"
STAMP="$(date +%Y-%m-%d)"

echo "==> M3 baseline 构建 · 代号 m3-${CODE}"
echo "    主工程: $ROOT"
echo "    输出:   $OUT"

require_dir() {
  if [[ ! -d "$1" ]]; then
    echo "ERROR: 缺少目录 $1" >&2
    exit 1
  fi
}

require_dir "$RECV/jiaxuan-m2-0616"
require_dir "$RECV/peixiao-m2-0616"
require_dir "$RECV/kaikai-m2-0616"

copy_module_base() {
  local name="$1"
  local src="$2"
  local dest="$OUT/${name}-m3-${CODE}-baseline"
  rm -rf "$dest"
  rsync -a --exclude '.env' --exclude '__pycache__' --exclude '*.pyc' \
    "$src/" "$dest/"
  echo "$dest"
}

sync_jiaxuan() {
  local JIA="$1"
  mkdir -p "$JIA/synced-from-main/server/routers" "$JIA/frontend/js"
  cp "$ROOT/server/routers/profile.py" "$JIA/synced-from-main/server/routers/"
  cp "$ROOT/server/completeness.py" "$JIA/synced-from-main/server/"
  cp "$ROOT/web/profile.html" "$JIA/frontend/profile.html"
  cp "$ROOT/web/js/shell.js" "$JIA/frontend/js/"
  cp "$ROOT/web/js/api-base.js" "$JIA/frontend/js/"
  cp "$ROOT/web/js/visit-common.js" "$JIA/frontend/js/"
  mkdir -p "$JIA/docs"
  cp "$ROOT/docs/M3并行开发手册-正式版.md" "$JIA/docs/"
  cp "$ROOT/docs/发给模块席-M3开包说明.md" "$JIA/docs/"
}

sync_peixiao() {
  local PEI="$1"
  mkdir -p "$PEI/synced-from-main/server/routers" "$PEI/frontend/js"
  cp "$ROOT/server/routers/visits.py" "$PEI/synced-from-main/server/routers/"
  cp "$ROOT/server/routers/brands.py" "$PEI/synced-from-main/server/routers/"
  cp "$ROOT/web/visit.html" "$PEI/frontend/visit.html"
  cp "$ROOT/web/js/visit-common.js" "$PEI/frontend/js/"
  cp "$ROOT/web/js/shell.js" "$PEI/frontend/js/"
  cp "$ROOT/web/js/api-base.js" "$PEI/frontend/js/"
  mkdir -p "$PEI/docs"
  cp "$ROOT/docs/M3并行开发手册-正式版.md" "$PEI/docs/"
  cp "$ROOT/docs/发给模块席-M3开包说明.md" "$PEI/docs/"
}

sync_kaikai() {
  local KAI="$1"
  mkdir -p "$KAI/synced-from-main/server/routers" "$KAI/synced-from-main/database" "$KAI/frontend/js"
  cp "$ROOT/server/routers/intel.py" "$KAI/synced-from-main/server/routers/"
  cp "$ROOT/database/migrate_intel_unify.sql" "$KAI/synced-from-main/database/" 2>/dev/null || true
  cp "$ROOT/web/intel.html" "$KAI/frontend/intel.html"
  cp "$ROOT/web/js/shell.js" "$KAI/frontend/js/"
  cp "$ROOT/web/js/api-base.js" "$KAI/frontend/js/"
  mkdir -p "$KAI/docs"
  cp "$ROOT/docs/M3并行开发手册-正式版.md" "$KAI/docs/"
  cp "$ROOT/docs/发给模块席-M3开包说明.md" "$KAI/docs/"
}

write_readme() {
  local file="$1"
  local who="$2"
  local tasks="$3"
  cat > "$file" <<EOF
# ${who} · M3 开工 baseline（m3-${CODE}）

> 生成：${STAMP} · 基线 tag \`prod-web-2026-06-18\` · **从 M2 收官主工程同步**

## 与 M2 baseline 的主要差异

| 项 | M2 | 本 M3 baseline |
|----|-----|----------------|
| 档案 Tab4 | 时间轴 → VisitCommon 日历同表 | 已同步 \`frontend/profile.html\` + \`visit-common.js\` |
| 拜访承诺筛选 | brand_id 后端 + 前端兜底 | 已同步 \`synced-from-main/server/routers/visits.py\` |
| intel briefing | 缓存 JSON 热修 | 已同步 \`synced-from-main/server/routers/intel.py\` |
| M3 目标 | 规则版 | **登录 + 数仓 + LLM 五路**（见 \`docs/M3并行开发手册-正式版.md\`） |

## 你的 M3 任务（摘要）

${tasks}

## 开发规则

1. **只改本包** → 完成后 zip 发 Max，文件名 \`<名>-m3-${CODE}.zip\`（**不要** \`-baseline\` 后缀）
2. **以 \`synced-from-main/\` 为准**对照主工程 API 路径
3. **LLM 未就绪**：用 \`LLM_ENABLED=false\` 或 mock；失败须降级 M2 规则版
4. **公共表加字段** → 群里 §1.4 字段申请，等 Max 批准
5. 详细手册：\`docs/M3并行开发手册-正式版.md\`

## 快速启动

见本包 \`README.md\`。看合并效果优先 **外网** http://117.72.211.51/ 硬刷新。
EOF
}

JIA=$(copy_module_base "jiaxuan" "$RECV/jiaxuan-m2-0616")
sync_jiaxuan "$JIA"
write_readme "$JIA/README-BASELINE.md" "佳璇" "$(cat <<'EOF'
- Tab1 `#profile-ai-blurb` 接 LLM + 降级 UI
- Tab2 竞争/机会接 `POST /api/brands/profile/{name_key}/ai/strategy` + 保留可编辑保存
- 数仓字段与档案指标对齐；M1/M2 回归 J-1～J-10
EOF
)"

PEI=$(copy_module_base "peixiao" "$RECV/peixiao-m2-0616")
sync_peixiao "$PEI"
write_readme "$PEI/README-BASELINE.md" "培翛" "$(cat <<'EOF'
- 拜访页按登录用户/负责品牌过滤
- 纪要 → LLM 抽待办/承诺（人工确认后落库）
- 提醒区可含 LLM 一句；M1/M2 回归 P-1～P-10
EOF
)"

KAI=$(copy_module_base "kaikai" "$RECV/kaikai-m2-0616")
sync_kaikai "$KAI"
write_readme "$KAI/README-BASELINE.md" "开开" "$(cat <<'EOF'
- 情报页品牌/权限过滤
- Feed + briefing LLM 摘要（写 intel_briefing_cache）
- CSV/分页 M2 回归；M1 回归 K-1～K-11
EOF
)"

REF="$OUT/sandtable-m3-reference-readonly"
rm -rf "$REF"
mkdir -p "$REF"
for item in server web database docs scripts deploy; do
  [[ -e "$ROOT/$item" ]] && rsync -a --exclude '.env' --exclude '__pycache__' --exclude '*.pyc' \
    "$ROOT/$item" "$REF/"
done
cp "$ROOT/docs/M3并行开发手册-正式版.md" "$REF/docs/"
cat > "$REF/README-只读对照.md" <<EOF
# sandtable M3 · 只读对照包（m3-${CODE}）

**不要在本目录开发。** 仅供对照 Max 主工程 M2 收官后效果。

外网：http://117.72.211.51/ · tag \`prod-web-2026-06-18\`

M3 开发请用各自 \`*-m3-${CODE}-baseline.zip\`。
EOF

echo "==> 打包 zip"
cd "$OUT"
for dir in jiaxuan-m3-${CODE}-baseline peixiao-m3-${CODE}-baseline kaikai-m3-${CODE}-baseline sandtable-m3-reference-readonly; do
  zip -r -q "${dir}.zip" "$dir"
  echo "    ${dir}.zip  ($(du -h "${dir}.zip" | cut -f1))"
done

cat > "$OUT/M3-baseline-清单.txt" <<EOF
M3 开工 baseline · ${STAMP} · 代号 m3-${CODE}

发给佳璇: jiaxuan-m3-${CODE}-baseline.zip
发给培翛: peixiao-m3-${CODE}-baseline.zip
发给开开: kaikai-m3-${CODE}-baseline.zip
全员对照: sandtable-m3-reference-readonly.zip

M3 交付包（三人 → Max，无 -baseline）:
  jiaxuan-m3-${CODE}.zip / peixiao-m3-${CODE}.zip / kaikai-m3-${CODE}.zip

手册: docs/M3并行开发手册-正式版.md
群公告: docs/发给模块席-M3开包说明.md
EOF

echo ""
echo "✅ 完成。清单: $OUT/M3-baseline-清单.txt"
ls -lh "$OUT"/*m3-${CODE}*.zip "$OUT"/sandtable-m3-reference-readonly.zip
