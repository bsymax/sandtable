#!/usr/bin/env bash
# M4 开工 baseline 包 · 从 M3 收官包 + 主工程 prod-web-m3-0622 同步
# 用法：bash scripts/build-m4-baseline-packages.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/deliverables"
RECV="$OUT/received"
CODE="0622"
STAMP="$(date +%Y-%m-%d)"
BASE_TAG="prod-web-m3-0622"

echo "==> M4 baseline 构建 · 代号 m4-${CODE}"
echo "    主工程: $ROOT"
echo "    基线:   ${BASE_TAG}"
echo "    输出:   $OUT"

require_dir() {
  if [[ ! -d "$1" ]]; then
    echo "ERROR: 缺少目录 $1" >&2
    exit 1
  fi
}

for name in jiaxuan peixiao kaikai; do
  require_dir "$RECV/${name}-m3-${CODE}"
done

copy_module_base() {
  local name="$1"
  local src="$2"
  local dest="$OUT/${name}-m4-${CODE}-baseline"
  rm -rf "$dest"
  rsync -a --exclude '.env' --exclude '__pycache__' --exclude '*.pyc' \
    "$src/" "$dest/"
  echo "$dest"
}

copy_docs_common() {
  local dest="$1"
  mkdir -p "$dest/docs/templates"
  cp "$ROOT/docs/M4并行开发手册-正式版.md" "$dest/docs/"
  cp "$ROOT/docs/发给模块席-M4开包说明.md" "$dest/docs/"
  cp "$ROOT/docs/M3并行开发手册-正式版.md" "$dest/docs/" 2>/dev/null || true
  cp "$ROOT/docs/templates/M4-联调纪要模板.md" "$dest/docs/templates/"
}

sync_jiaxuan() {
  local JIA="$1"
  mkdir -p "$JIA/synced-from-main/server/routers" "$JIA/frontend/js" "$JIA/data/dw"
  cp "$ROOT/server/routers/profile.py" "$JIA/synced-from-main/server/routers/"
  cp "$ROOT/server/completeness.py" "$JIA/synced-from-main/server/"
  cp "$ROOT/web/profile.html" "$JIA/frontend/profile.html"
  cp "$ROOT/web/js/shell.js" "$JIA/frontend/js/"
  cp "$ROOT/web/js/api-base.js" "$JIA/frontend/js/"
  cp "$ROOT/web/js/visit-common.js" "$JIA/frontend/js/"
  cp "$ROOT/web/js/auth.js" "$JIA/frontend/js/"
  cp "$ROOT/web/js/m3-config.js" "$JIA/frontend/js/"
  cp "$ROOT/data/dw/brand_metrics_weekly.csv" "$JIA/data/dw/"
  cp "$ROOT/data/dw/bi_mapping.json.example" "$JIA/data/dw/"
  cp "$ROOT/data/brands_master.json" "$JIA/data/"
  cp "$ROOT/docs/品牌主数据-v1.md" "$JIA/docs/"
  cp "$ROOT/docs/数仓字段口径-v1.md" "$JIA/docs/"
  copy_docs_common "$JIA"
}

sync_peixiao() {
  local PEI="$1"
  mkdir -p "$PEI/synced-from-main/server/routers" "$PEI/frontend/js" "$PEI/docs/templates" "$PEI/data"
  cp "$ROOT/server/routers/visits.py" "$PEI/synced-from-main/server/routers/"
  cp "$ROOT/server/routers/brands.py" "$PEI/synced-from-main/server/routers/"
  cp "$ROOT/web/visit.html" "$PEI/frontend/visit.html"
  cp "$ROOT/web/js/visit-common.js" "$PEI/frontend/js/"
  cp "$ROOT/web/js/shell.js" "$PEI/frontend/js/"
  cp "$ROOT/web/js/api-base.js" "$PEI/frontend/js/"
  cp "$ROOT/web/js/auth.js" "$PEI/frontend/js/"
  cp "$ROOT/web/js/m3-config.js" "$PEI/frontend/js/"
  cp "$ROOT/web/js/m3-mock-llm.js" "$PEI/frontend/js/"
  cp "$ROOT/docs/templates/M4-联调纪要模板.md" "$PEI/docs/M4-联调纪要模板.md"
  cp "$ROOT/data/brands_master.json" "$PEI/data/"
  cp "$ROOT/docs/品牌主数据-v1.md" "$PEI/docs/"
  copy_docs_common "$PEI"
}

sync_kaikai() {
  local KAI="$1"
  mkdir -p "$KAI/synced-from-main/server/routers" "$KAI/synced-from-main/database" "$KAI/frontend/js" "$KAI/data/dw" "$KAI/data"
  cp "$ROOT/server/routers/intel.py" "$KAI/synced-from-main/server/routers/"
  cp "$ROOT/database/migrate_intel_unify.sql" "$KAI/synced-from-main/database/" 2>/dev/null || true
  cp "$ROOT/web/intel.html" "$KAI/frontend/intel.html"
  cp "$ROOT/web/js/shell.js" "$KAI/frontend/js/"
  cp "$ROOT/web/js/api-base.js" "$KAI/frontend/js/"
  cp "$ROOT/web/js/auth.js" "$KAI/frontend/js/"
  cp "$ROOT/web/js/m3-config.js" "$KAI/frontend/js/"
  cp "$ROOT/data/dw/brand_metrics_weekly.csv" "$KAI/data/dw/"
  mkdir -p "$KAI/docs"
  cp "$ROOT/data/brands_master.json" "$KAI/data/"
  cp "$ROOT/docs/品牌主数据-v1.md" "$KAI/docs/"
  copy_docs_common "$KAI"
}

write_patchlog() {
  local file="$1"
  local who="$2"
  cat > "$file" <<EOF
# ${who} · M4 开发包（*-m4-${CODE}.zip）

> **基线**：*-m4-${CODE}-baseline · **基线 tag** \`${BASE_TAG}\`
> **手册**：\`docs/M4并行开发手册-正式版.md\` §3.2 · §3.4

## 改动清单

（按 D-*-M4 编号填写）

### 示例
- **frontend/xxx.html**: 说明
- **依赖 Max**：M4-A / M4-B / M4-C / M4-D

## 自测勾选

| 项 | ☐ |
|----|---|
| 本地或外网冒烟 | ☐ |
| 对应 D-*-M4 表 | ☐ |
| \`readonly\` 只读（如适用） | ☐ |

## 发给 Max

- 文件名：\`<名>-m4-${CODE}.zip\`（**不要** \`-baseline\` 后缀）
EOF
}

write_readme() {
  local file="$1"
  local who="$2"
  local module="$3"
  local tasks="$4"
  local extra="${5:-}"
  cat > "$file" <<EOF
# ${who} · M4 开工 baseline（m4-${CODE}）

> 生成：${STAMP} · 基线 tag \`${BASE_TAG}\` · **从 M3 收官包 + 主工程同步**

## 与 M3 baseline 的主要差异

| 项 | M3 | 本 M4 baseline |
|----|-----|----------------|
| 角色 | 登录 + 品牌过滤 | **\`readonly\` 禁写** · 四角色回归（等 Max **M4-A**） |
| LLM | 五路 + 降级 | **审计 + 配额**（等 Max **M4-B**） |
| 数仓 | 样例 CSV | **BI 真 GMV 首接**（等 Max **M4-C**） |
| 工程 | 外网 | + **泰山预发**（Max **M4-D**） |
| 不做 | — | 驾驶舱 · 50人推广 · 压测 → **M6+** |

## 你的 M4 任务（摘要）

${tasks}

${extra}

## Max 里程碑（看群公告）

| 里程碑 | 内容 | 目标日 |
|--------|------|--------|
| M4-A | 角色读写 | T0+2 |
| M4-B | LLM 审计/配额 | T0+4 |
| M4-C | 数仓 BI 首接 | T0+6 |
| M4-D | 预发 + 上云 | T0+8 |

## 开发规则

1. **只改本包** → \`<名>-m4-${CODE}.zip\` 发 Max
2. **以 \`synced-from-main/\` 对照**主工程 API
3. **LLM 失败不算 bug** · 须降级规则版
4. 新字段 → 群里字段申请
5. 手册：\`docs/M4并行开发手册-正式版.md\`
6. 外网验收：http://117.72.211.51/ · Cmd+Shift+R

## 快速启动

见本包 \`README.md\`。${module} 主改 \`frontend/${module}\`。
EOF
}

JIA=$(copy_module_base "jiaxuan" "$RECV/jiaxuan-m3-${CODE}")
sync_jiaxuan "$JIA"
write_patchlog "$JIA/PATCHLOG.md" "佳璇"
write_readme "$JIA/README-BASELINE.md" "佳璇" "profile.html" "$(cat <<'EOF'
- **牵头 D-J-M4-1**：5 品牌 GMV 与 BI 导出逐格对照（截图）
- 填写 `docs/数仓字段口径-v1.md`（与业务 BI 对齐）
- 档案「数据截至 YYYY-Wxx」+ 指标空值样式
- Tab1/Tab2 Prompt 与降级文案调优
- `readonly` 禁保存档案；J-1～J-10 + M3 D-J 回归
EOF
)" "$(cat <<'EOF'

## 包内专供

- `docs/数仓字段口径-v1.md` — 你维护，M4 定稿
- `data/dw/bi_mapping.json.example` — 给 Max 导入映射参考
- `data/dw/brand_metrics_weekly.csv` — CSV 列格式样例
EOF
)"

PEI=$(copy_module_base "peixiao" "$RECV/peixiao-m3-${CODE}")
sync_peixiao "$PEI"
write_patchlog "$PEI/PATCHLOG.md" "培翛"
write_readme "$PEI/README-BASELINE.md" "培翛" "visit.html" "$(cat <<'EOF'
- **牵头 D-P-M4-0/1**：组织三人联调冒烟 · 外网+预发 P-1～P-10
- 拜访/提醒区「经营数据已更新至 **Wxx**」（读 `brand_metrics` 最新周）
- 纪要 LLM 边界：截断/JSON 失败/**确认后才落库**
- `readonly` 拜访禁写 UI + 回归
- 填写 `docs/M4-联调纪要模板.md` 并发群
EOF
)" "$(cat <<'EOF'

## 包内专供

- `docs/M4-联调纪要模板.md` — **你牵头**填写 · D-P-M4-1 验收附件
EOF
)"

KAI=$(copy_module_base "kaikai" "$RECV/kaikai-m3-${CODE}")
sync_kaikai "$KAI"
write_patchlog "$KAI/PATCHLOG.md" "开开"
write_readme "$KAI/README-BASELINE.md" "开开" "intel.html" "$(cat <<'EOF'
- briefing/Feed LLM 质量；cache key 含 `period_value`
- CSV 导入行级错误提示 + 模板
- briefing 叙事与最新周 GMV 不矛盾（D-K-M4-2）
- `readonly` 禁录入/改预警
- K-1～K-11 + M3 D-K 回归
EOF
)"

# 更新各包 README 标题 M3→M4 提示
for pkg in "$JIA" "$PEI" "$KAI"; do
  if [[ -f "$pkg/README.md" ]]; then
    sed -i '' 's/M3 ·/M4 ·/g; s/m3-0622/m4-0622/g; s/M3 主改/M4 主改/g' "$pkg/README.md" 2>/dev/null || \
      sed -i 's/M3 ·/M4 ·/g; s/m3-0622/m4-0622/g; s/M3 主改/M4 主改/g' "$pkg/README.md" 2>/dev/null || true
  fi
done

REF="$OUT/sandtable-m4-reference-readonly"
rm -rf "$REF"
mkdir -p "$REF"
for item in server web database docs scripts deploy data; do
  [[ -e "$ROOT/$item" ]] && rsync -a --exclude '.env' --exclude '__pycache__' --exclude '*.pyc' \
    "$ROOT/$item" "$REF/"
done
cp "$ROOT/docs/M4并行开发手册-正式版.md" "$REF/docs/"
cat > "$REF/README-只读对照.md" <<EOF
# sandtable M4 · 只读对照包（m4-${CODE}）

**不要在本目录开发。** 仅供对照 Max 主工程 M3 收官后效果。

外网：http://117.72.211.51/ · tag \`${BASE_TAG}\`

M4 开发请用各自 \`*-m4-${CODE}-baseline.zip\`。
EOF

echo "==> 打包 zip"
cd "$OUT"
for dir in jiaxuan-m4-${CODE}-baseline peixiao-m4-${CODE}-baseline kaikai-m4-${CODE}-baseline sandtable-m4-reference-readonly; do
  zip -r -q "${dir}.zip" "$dir"
  echo "    ${dir}.zip  ($(du -h "${dir}.zip" | cut -f1))"
done

cat > "$OUT/M4-baseline-清单.txt" <<EOF
M4 开工 baseline · ${STAMP} · 代号 m4-${CODE} · 基线 ${BASE_TAG}

发给佳璇: jiaxuan-m4-${CODE}-baseline.zip
发给培翛: peixiao-m4-${CODE}-baseline.zip
发给开开: kaikai-m4-${CODE}-baseline.zip
全员对照: sandtable-m4-reference-readonly.zip

M4 交付包（三人 → Max，无 -baseline）:
  jiaxuan-m4-${CODE}.zip / peixiao-m4-${CODE}.zip / kaikai-m4-${CODE}.zip

手册: docs/M4并行开发手册-正式版.md
群公告: docs/发给模块席-M4开包说明.md

交包:
  首包 T0+5 18:00 · 终包 T0+8 18:00
EOF

echo ""
echo "✅ 完成。清单: $OUT/M4-baseline-清单.txt"
ls -lh "$OUT"/*m4-${CODE}*.zip "$OUT"/sandtable-m4-reference-readonly.zip 2>/dev/null
