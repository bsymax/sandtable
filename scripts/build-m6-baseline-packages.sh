#!/usr/bin/env bash
# M6 开工 baseline 包 · 从 M5 收官包 + 主工程 prod-web-m5-pilot 同步
# 用法：bash scripts/build-m6-baseline-packages.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/deliverables"
RECV="$OUT/received"
CODE="trial"
STAMP="$(date +%Y-%m-%d)"
BASE_TAG="prod-web-m5-pilot"

echo "==> M6 baseline 构建 · 代号 m6-${CODE}"
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
  case "$name" in
    jiaxuan) require_dir "$RECV/jiaxuan-m5-0624" ;;
    peixiao) require_dir "$RECV/peixiao-m5-062402" ;;
    kaikai)  require_dir "$RECV/kaikai-m5-0624" ;;
  esac
done

copy_module_base() {
  local name="$1"
  local src="$2"
  local dest="$OUT/${name}-m6-${CODE}-baseline"
  rm -rf "$dest"
  rsync -a --exclude '.env' --exclude '__pycache__' --exclude '*.pyc' --exclude '*.xlsx' \
    "$src/" "$dest/"
  echo "$dest"
}

copy_docs_common() {
  local dest="$1"
  mkdir -p "$dest/docs/templates"
  cp "$ROOT/docs/M6并行开发手册-正式版.md" "$dest/docs/"
  cp "$ROOT/docs/发给模块席-M6开包说明.md" "$dest/docs/"
  cp "$ROOT/docs/M5并行开发手册-正式版.md" "$dest/docs/" 2>/dev/null || true
  cp "$ROOT/docs/templates/M4-联调纪要模板.md" "$dest/docs/templates/" 2>/dev/null || true
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
  cp "$ROOT/docs/templates/M4-联调纪要模板.md" "$PEI/docs/M4-联调纪要模板.md" 2>/dev/null || true
  cp "$ROOT/data/brands_master.json" "$PEI/data/"
  cp "$ROOT/docs/品牌主数据-v1.md" "$PEI/docs/"
  copy_docs_common "$PEI"
  cat > "$PEI/docs/templates/visit-history-import-readme.md" <<'EOF'
# 历史拜访 Excel 导入说明（培翛 · M6）

采销按模板填写 **已完成的历史拜访 + 记录内容**，由培翛页面导入。

## 模板字段（首版）

| 列名 | 必填 | 说明 |
|------|------|------|
| brand_key | ✅ | 品牌 key 或中文名 |
| visit_date | ✅ | YYYY-MM-DD |
| visit_type | | regular / urgent / renewal |
| purpose | ✅ | 拜访目的 |
| participants | | 参与人 |
| topics | | 会谈议题 |
| commitments_raw | | 承诺原文 |
| undone_items | | 未达成 |
| relation_change | | up / flat / down |
| next_visit_date | | 下次拜访日期 |

## 重复导入

同一 brand + visit_date + purpose 已存在时，须提示 **覆盖** 或 **新增**；导入结束给出汇总。

详见 `docs/M6并行开发手册-正式版.md` 附录 E。
EOF
}

sync_kaikai() {
  local KAI="$1"
  mkdir -p "$KAI/synced-from-main/server/routers" "$KAI/synced-from-main/database" \
    "$KAI/frontend/js" "$KAI/data/dw" "$KAI/data" "$KAI/docs/templates"
  cp "$ROOT/server/routers/intel.py" "$KAI/synced-from-main/server/routers/"
  cp "$ROOT/database/migrate_intel_unify.sql" "$KAI/synced-from-main/database/" 2>/dev/null || true
  cp "$ROOT/web/intel.html" "$KAI/frontend/intel.html"
  cp "$ROOT/web/index.html" "$KAI/frontend/index.html"
  cp "$ROOT/web/js/shell.js" "$KAI/frontend/js/"
  cp "$ROOT/web/js/api-base.js" "$KAI/frontend/js/"
  cp "$ROOT/web/js/auth.js" "$KAI/frontend/js/"
  cp "$ROOT/web/js/m3-config.js" "$KAI/frontend/js/"
  cp "$ROOT/data/dw/brand_metrics_weekly.csv" "$KAI/data/dw/"
  cp "$ROOT/data/brands_master.json" "$KAI/data/"
  cp "$ROOT/docs/品牌主数据-v1.md" "$KAI/docs/"
  copy_docs_common "$KAI"
  mkdir -p "$KAI/docs/templates"
  cat > "$KAI/docs/templates/pilot-users-m6.example.csv" <<'EOF'
username,display_name,role,brand_keys,dept
zhangsan,张三,bd,jomoo,建材业务部-KA卫浴组
lisi,李四,bd,jc_a,建材业务部-基础建材组
wangwu,王五,readonly,"jomoo,jc_a",建材业务部-KA卫浴组
EOF
  cat > "$KAI/docs/templates/pilot-users-changelog.md" <<'EOF'
# M6 正式名单变更台账（开开维护）

| 日期 | 变更 | username | 说明 |
|------|------|----------|------|
| YYYY-MM-DD | 新增 | | |
EOF
  cat > "$KAI/docs/templates/pilot-spotcheck.md" <<'EOF'
# M6 名单 spot-check（导入后填写 · ≥50 人）

| role | username | 登录 | 情报录入 | 备注 |
|------|----------|------|----------|------|
| bd | | ☐ | ☐ | |
| manager | | ☐ | ☐ | |
| readonly | | ☐ | ☐ | |
EOF
}

write_patchlog() {
  local file="$1"
  local who="$2"
  cat > "$file" <<EOF
# ${who} · M6 开发包（*-m6-${CODE}.zip）

> **基线**：*-m6-${CODE}-baseline · **基线 tag** \`${BASE_TAG}\`
> **手册**：\`docs/M6并行开发手册-正式版.md\` §3.2 · §3.4

## 改动清单

（按 D-*-M6 编号填写）

## 自测勾选

| 项 | ☐ |
|----|---|
| 附录 C 无「厨小事业部」 | ☐ |
| 对应 D-*-M6 表 | ☐ |
| \`readonly\` 只读（如适用） | ☐ |

## 发给 Max

- 文件名：\`<名>-m6-${CODE}.zip\`（**不要** \`-baseline\` 后缀）
EOF
}

write_readme() {
  local file="$1"
  local who="$2"
  local module="$3"
  local tasks="$4"
  local extra="${5:-}"
  cat > "$file" <<EOF
# ${who} · M6 开工 baseline（m6-${CODE}）

> 生成：${STAMP} · 基线 tag \`${BASE_TAG}\` · **从 M5 收官包 + 主工程同步**

## 与 M5 baseline 的主要差异

| 项 | M5 | 本 M6 baseline |
|----|-----|----------------|
| 目标 | 50～100 试点 · UI 打磨 | **正式 50 采销** · **双部门十品牌** |
| 组织 | 厨小 mock 文案 | **建材业务部-KA卫浴组 / 基础建材组** |
| 品牌 | 5 卫浴 | **10 品牌**（基础建材 A～E 占位） |
| 拜访 | 在线录入 | **历史拜访 Excel 导入** |
| 情报 | CSV 运维 | **单条新闻录入** + 隐藏 mock |
| 工具包 | 无 | **谈参 + 品牌报告**（佳璇） |
| 泰山切流 | → M6 | → **M7+** |

## 你的 M6 任务（摘要）

${tasks}

${extra}

## Max 里程碑（看群公告）

| 里程碑 | 内容 | 目标 |
|--------|------|------|
| M6-A | 10 品牌 · 厨小清零 · mock 过滤 | D0+1 |
| M6-B | 50 人统一初始密码导入 | **本周** |
| M6-C | 工具包壳层 · 顶栏 dept | D0+3 |
| M6-D | 合并三包 · tag prod-web-m6-trial | D0+5 |

## 开发规则

1. **只改本包** → \`<名>-m6-${CODE}.zip\` 发 Max
2. **以 \`synced-from-main/\` 对照**主工程 API
3. **不要**改 users 表 / 登录改密 API / admin 页 / 统一密码脚本（Max 独占）
4. **全站去掉「厨小事业部」**（附录 C）
5. 手册：\`docs/M6并行开发手册-正式版.md\`
6. 外网：http://117.72.211.51/ · Cmd+Shift+R

## 快速启动

见本包 \`README.md\`。${module} 主改 \`frontend/${module}\`。
EOF
}

JIA=$(copy_module_base "jiaxuan" "$RECV/jiaxuan-m5-0624")
sync_jiaxuan "$JIA"
write_patchlog "$JIA/PATCHLOG.md" "佳璇"
write_readme "$JIA/README-BASELINE.md" "佳璇" "profile.html" "$(cat <<'EOF'
- **部门–品牌主数据**：替换 jc_a～jc_e 占位为真名（PATCHLOG 附映射表）
- 10 品牌档案/数仓 · FAQ/SLA 同步
- **不做** 工具包谈参/品牌报告（培翛 peixiao-m6-0630 已交付）
EOF
)"

PEI=$(copy_module_base "peixiao" "$RECV/peixiao-m5-062402")
sync_peixiao "$PEI"
write_patchlog "$PEI/PATCHLOG.md" "培翛"
write_readme "$PEI/README-BASELINE.md" "培翛" "visit.html" "$(cat <<'EOF'
- **历史拜访 Excel 导入**：模板 + 上传预览 + 覆盖/新增提示
- 演示拜访 mock **默认不展示**
- **工具包 · 谈参 + 品牌报告**（shell 入口 + toolkit/ 两页）
- visit 回归 · 附录 E 字段对齐
EOF
)" "$(cat <<'EOF'

## 包内专供

- `docs/templates/visit-history-import-readme.md` — 导入字段说明
EOF
)"

KAI=$(copy_module_base "kaikai" "$RECV/kaikai-m5-0624")
sync_kaikai "$KAI"
write_patchlog "$KAI/PATCHLOG.md" "开开"
write_readme "$KAI/README-BASELINE.md" "开开" "intel.html + index.html" "$(cat <<'EOF'
- **新闻单条录入**（bd + admin）
- 假情报/预警 mock **默认不展示**
- **pilot-users-m6.csv ≥50 行** · 含 dept · 变更台账
- **工作群公告**（附录 H · 统一初始密码）
- index/intel 无「厨小」回归
EOF
)" "$(cat <<'EOF'

## 包内专供（名单）

- `docs/templates/pilot-users-m6.example.csv` — M6 格式样例
- `docs/templates/pilot-users-changelog.md` — 变更台账
- `docs/templates/pilot-spotcheck.md` — 导入后抽测
EOF
)"

for pkg in "$JIA" "$PEI" "$KAI"; do
  if [[ -f "$pkg/README.md" ]]; then
    sed -i '' 's/M5 ·/M6 ·/g; s/m5-pilot/m6-trial/g; s/M5 主改/M6 主改/g' "$pkg/README.md" 2>/dev/null || \
      sed -i 's/M5 ·/M6 ·/g; s/m5-pilot/m6-trial/g; s/M5 主改/M6 主改/g' "$pkg/README.md" 2>/dev/null || true
  fi
done

REF="$OUT/sandtable-m6-reference-readonly"
rm -rf "$REF"
mkdir -p "$REF"
for item in server web database docs scripts deploy data; do
  [[ -e "$ROOT/$item" ]] && rsync -a --exclude '.env' --exclude '__pycache__' --exclude '*.pyc' --exclude '*.xlsx' \
    "$ROOT/$item" "$REF/"
done
cp "$ROOT/docs/M6并行开发手册-正式版.md" "$REF/docs/"
cp "$ROOT/docs/发给模块席-M6开包说明.md" "$REF/docs/"
cat > "$REF/README-只读对照.md" <<EOF
# sandtable M6 · 只读对照包（m6-${CODE}）

**不要在本目录开发。** 仅供对照 Max 主工程 M5 收官后效果。

外网：http://117.72.211.51/ · tag \`${BASE_TAG}\`

M6 开发请用各自 \`*-m6-${CODE}-baseline.zip\`。
EOF

echo "==> 打包 zip"
cd "$OUT"
for dir in jiaxuan-m6-${CODE}-baseline peixiao-m6-${CODE}-baseline kaikai-m6-${CODE}-baseline sandtable-m6-reference-readonly; do
  rm -f "${dir}.zip"
  zip -r -q "${dir}.zip" "$dir"
  echo "    ${dir}.zip  ($(du -h "${dir}.zip" | cut -f1))"
done

cat > "$OUT/M6-baseline-清单.txt" <<EOF
M6 开工 baseline · ${STAMP} · 代号 m6-${CODE} · 基线 ${BASE_TAG}

发给佳璇: jiaxuan-m6-${CODE}-baseline.zip
发给培翛: peixiao-m6-${CODE}-baseline.zip
发给开开: kaikai-m6-${CODE}-baseline.zip
全员对照: sandtable-m6-reference-readonly.zip

M6 交付包（三人 → Max，无 -baseline）:
  jiaxuan-m6-${CODE}.zip / peixiao-m6-${CODE}.zip / kaikai-m6-${CODE}.zip

手册: docs/M6并行开发手册-正式版.md
群公告: docs/发给模块席-M6开包说明.md

关键节点:
  本周 开开 pilot-users-m6.csv（≥50 行）
  D0+2 首包 · D0+5 终包 · tag prod-web-m6-trial
EOF

echo ""
echo "✅ 完成。清单: $OUT/M6-baseline-清单.txt"
ls -lh "$OUT"/*m6-${CODE}*.zip "$OUT"/sandtable-m6-reference-readonly.zip 2>/dev/null
