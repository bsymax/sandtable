#!/usr/bin/env bash
# M5 开工 baseline 包 · 从 M4 收官包 + 主工程 prod-web-m4-0622 同步
# 用法：bash scripts/build-m5-baseline-packages.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/deliverables"
RECV="$OUT/received"
CODE="pilot"
STAMP="$(date +%Y-%m-%d)"
BASE_TAG="prod-web-m4-0622"

echo "==> M5 baseline 构建 · 代号 m5-${CODE}"
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
  require_dir "$RECV/${name}-m4-0622"
done

copy_module_base() {
  local name="$1"
  local src="$2"
  local dest="$OUT/${name}-m5-${CODE}-baseline"
  rm -rf "$dest"
  rsync -a --exclude '.env' --exclude '__pycache__' --exclude '*.pyc' --exclude '*.xlsx' \
    "$src/" "$dest/"
  echo "$dest"
}

copy_docs_common() {
  local dest="$1"
  mkdir -p "$dest/docs/templates"
  cp "$ROOT/docs/M5并行开发手册-正式版.md" "$dest/docs/"
  cp "$ROOT/docs/发给模块席-M5开包说明.md" "$dest/docs/"
  cp "$ROOT/docs/M4并行开发手册-正式版.md" "$dest/docs/" 2>/dev/null || true
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
  cat > "$KAI/docs/templates/pilot-users-v1.example.csv" <<'EOF'
username,display_name,role,brand_keys,dept
zhangsan,张三,bd,jomoo,厨小事业部·采销一组
lisi,李四,manager,"jomoo,arrow",厨小事业部·采销二组
wangwu,王五,readonly,micoe,厨小事业部·负责人
EOF
  cat > "$KAI/docs/templates/pilot-users-changelog.md" <<'EOF'
# 试点名单变更台账（开开维护）

| 日期 | 变更 | username | 说明 |
|------|------|----------|------|
| YYYY-MM-DD | 新增 | | |
EOF
  cat > "$KAI/docs/templates/pilot-spotcheck.md" <<'EOF'
# 名单 spot-check（导入后填写）

| role | username | 登录 | 情报录入/简报 | 备注 |
|------|----------|------|---------------|------|
| bd | | ☐ | ☐ | |
| manager | | ☐ | ☐ | |
| readonly | | ☐ | ☐ | |
EOF
}

write_patchlog() {
  local file="$1"
  local who="$2"
  cat > "$file" <<EOF
# ${who} · M5 开发包（*-m5-${CODE}.zip）

> **基线**：*-m5-${CODE}-baseline · **基线 tag** \`${BASE_TAG}\`
> **手册**：\`docs/M5并行开发手册-正式版.md\` §3.2 · §3.4

## 改动清单

（按 D-*-M5 编号填写）

## 自测勾选

| 项 | ☐ |
|----|---|
| 附录 G 本模块行 | ☐ |
| 对应 D-*-M5 表 | ☐ |
| \`readonly\` 只读（如适用） | ☐ |

## 发给 Max

- 文件名：\`<名>-m5-${CODE}.zip\`（**不要** \`-baseline\` 后缀）
EOF
}

write_readme() {
  local file="$1"
  local who="$2"
  local module="$3"
  local tasks="$4"
  local extra="${5:-}"
  cat > "$file" <<EOF
# ${who} · M5 开工 baseline（m5-${CODE}）

> 生成：${STAMP} · 基线 tag \`${BASE_TAG}\` · **从 M4 收官包 + 主工程同步**

## 与 M4 baseline 的主要差异

| 项 | M4 | 本 M5 baseline |
|----|-----|----------------|
| 目标 | 四角色 · BI · LLM 审计 | **50～100 人试点** · **UI 附录 G** |
| 账号 | 测试 sand123 | **开开名单 CSV** → Max 导入（附录 J） |
| 新增 | — | 改密/admin（等 Max **M5-A/B**） |
| 不做 | 驾驶舱 | 泰山切流 → **M6** |

## 你的 M5 任务（摘要）

${tasks}

${extra}

## Max 里程碑（看群公告）

| 里程碑 | 内容 | 目标日 |
|--------|------|--------|
| M5-A | migration + 改密 API | D0+2 |
| M5-B | admin 用户管理 | D0+4 |
| M5-C | 导入开开 CSV v1 | D0+5 |
| M5-D | shell/login 公共 UI | D0+6 |
| M5-E/F | 备份 · tag | D0+8 |

## 开发规则

1. **只改本包** → \`<名>-m5-${CODE}.zip\` 发 Max
2. **以 \`synced-from-main/\` 对照**主工程 API
3. **不要**改 users 表 / 登录改密 API / admin 页（Max 独占）
4. UI 只改 **附录 G 本模块行**
5. 手册：\`docs/M5并行开发手册-正式版.md\`
6. 外网：http://117.72.211.51/ · Cmd+Shift+R

## 快速启动

见本包 \`README.md\`。${module} 主改 \`frontend/${module}\`。
EOF
}

JIA=$(copy_module_base "jiaxuan" "$RECV/jiaxuan-m4-0622")
sync_jiaxuan "$JIA"
write_patchlog "$JIA/PATCHLOG.md" "佳璇"
write_readme "$JIA/README-BASELINE.md" "佳璇" "profile.html" "$(cat <<'EOF'
- 附录 G **profile.html** 行（去 M4-A 等里程碑文案）
- 档案试点 FAQ（含 readonly 说明）
- 数仓 SLA · BI 周更窗口文档
- J 表回归（可抽名单内 bd 账号）
EOF
)"

PEI=$(copy_module_base "peixiao" "$RECV/peixiao-m4-0622")
sync_peixiao "$PEI"
write_patchlog "$PEI/PATCHLOG.md" "培翛"
write_readme "$PEI/README-BASELINE.md" "培翛" "visit.html" "$(cat <<'EOF'
- 附录 G **visit.html** 行
- **试点巡检**首周执行（账号从开开名单抽）
- 多采销并行拜访场景回归
- 拜访 FAQ（1 页）
EOF
)" "$(cat <<'EOF'

## 包内专供

- 巡检模板见手册 **附录 I**
EOF
)"

KAI=$(copy_module_base "kaikai" "$RECV/kaikai-m4-0622")
sync_kaikai "$KAI"
write_patchlog "$KAI/PATCHLOG.md" "开开"
write_readme "$KAI/README-BASELINE.md" "开开" "intel.html + index.html" "$(cat <<'EOF'
- **牵头试点名单**：收 raw 表 → 清洗 CSV · **D0+2 18:00** 交 v1（附录 J）
- 附录 G **intel.html** + **index.html 工作台**（G.6）
- 推广说明：登录/改密/情报录入段
- 名单 spot-check + K 表回归
EOF
)" "$(cat <<'EOF'

## 包内专供（名单）

- `docs/templates/pilot-users-v1.example.csv` — F.5 格式样例
- `docs/templates/pilot-users-changelog.md` — 变更台账
- `docs/templates/pilot-spotcheck.md` — 导入后抽测记录
EOF
)"

for pkg in "$JIA" "$PEI" "$KAI"; do
  if [[ -f "$pkg/README.md" ]]; then
    sed -i '' 's/M4 ·/M5 ·/g; s/m4-0622/m5-pilot/g; s/M4 主改/M5 主改/g' "$pkg/README.md" 2>/dev/null || \
      sed -i 's/M4 ·/M5 ·/g; s/m4-0622/m5-pilot/g; s/M4 主改/M5 主改/g' "$pkg/README.md" 2>/dev/null || true
  fi
done

REF="$OUT/sandtable-m5-reference-readonly"
rm -rf "$REF"
mkdir -p "$REF"
for item in server web database docs scripts deploy data; do
  [[ -e "$ROOT/$item" ]] && rsync -a --exclude '.env' --exclude '__pycache__' --exclude '*.pyc' --exclude '*.xlsx' \
    "$ROOT/$item" "$REF/"
done
cp "$ROOT/docs/M5并行开发手册-正式版.md" "$REF/docs/"
cp "$ROOT/docs/发给模块席-M5开包说明.md" "$REF/docs/"
cat > "$REF/README-只读对照.md" <<EOF
# sandtable M5 · 只读对照包（m5-${CODE}）

**不要在本目录开发。** 仅供对照 Max 主工程 M4 收官后效果。

外网：http://117.72.211.51/ · tag \`${BASE_TAG}\`

M5 开发请用各自 \`*-m5-${CODE}-baseline.zip\`。
EOF

echo "==> 打包 zip"
cd "$OUT"
for dir in jiaxuan-m5-${CODE}-baseline peixiao-m5-${CODE}-baseline kaikai-m5-${CODE}-baseline sandtable-m5-reference-readonly; do
  rm -f "${dir}.zip"
  zip -r -q "${dir}.zip" "$dir"
  echo "    ${dir}.zip  ($(du -h "${dir}.zip" | cut -f1))"
done

cat > "$OUT/M5-baseline-清单.txt" <<EOF
M5 开工 baseline · ${STAMP} · 代号 m5-${CODE} · 基线 ${BASE_TAG}

发给佳璇: jiaxuan-m5-${CODE}-baseline.zip
发给培翛: peixiao-m5-${CODE}-baseline.zip
发给开开: kaikai-m5-${CODE}-baseline.zip
全员对照: sandtable-m5-reference-readonly.zip

M5 交付包（三人 → Max，无 -baseline）:
  jiaxuan-m5-${CODE}.zip / peixiao-m5-${CODE}.zip / kaikai-m5-${CODE}.zip

手册: docs/M5并行开发手册-正式版.md
群公告: docs/发给模块席-M5开包说明.md

关键节点:
  D0+2 18:00 开开 pilot-users-v1.csv
  D0+5 18:00 首包 · D0+8 18:00 终包
EOF

echo ""
echo "✅ 完成。清单: $OUT/M5-baseline-清单.txt"
ls -lh "$OUT"/*m5-${CODE}*.zip "$OUT"/sandtable-m5-reference-readonly.zip 2>/dev/null
