#!/usr/bin/env bash
# 佳璇 M6 baseline 补发包 · 同步主工程最新（含 peixiao-m6-0630 / kaikai-m6-0630 合并态）
# 用法：bash scripts/build-jiaxuan-m6-baseline.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/deliverables"
RECV="$OUT/received"
CODE="trial"
STAMP="$(date +%Y-%m-%d)"
BASE_NOTE="主工程 M6 工作区 · peixiao-m6-0630 + kaikai-m6-0630 已合并"

echo "==> 佳璇 M6 baseline 补发 · 代号 m6-${CODE}"
echo "    主工程: $ROOT"
echo "    基线说明: ${BASE_NOTE}"
echo "    输出:   $OUT/jiaxuan-m6-${CODE}-baseline.zip"

require_dir() {
  if [[ ! -d "$1" ]]; then
    echo "ERROR: 缺少目录 $1" >&2
    exit 1
  fi
}

require_dir "$RECV/jiaxuan-m5-0624"

JIA="$OUT/jiaxuan-m6-${CODE}-baseline"
rm -rf "$JIA"
rsync -a --exclude '.env' --exclude '__pycache__' --exclude '*.pyc' --exclude '*.xlsx' \
  "$RECV/jiaxuan-m5-0624/" "$JIA/"

mkdir -p "$JIA/synced-from-main/server/routers" "$JIA/frontend/js" "$JIA/data/dw" "$JIA/docs/templates"
cp "$ROOT/server/routers/profile.py" "$JIA/synced-from-main/server/routers/"
cp "$ROOT/server/completeness.py" "$JIA/synced-from-main/server/"
cp "$ROOT/server/dw_sync.py" "$JIA/synced-from-main/server/" 2>/dev/null || true
cp "$ROOT/web/profile.html" "$JIA/frontend/profile.html"
cp "$ROOT/web/js/shell.js" "$JIA/frontend/js/"
cp "$ROOT/web/js/api-base.js" "$JIA/frontend/js/"
cp "$ROOT/web/js/visit-common.js" "$JIA/frontend/js/"
cp "$ROOT/web/js/auth.js" "$JIA/frontend/js/"
cp "$ROOT/web/js/m3-config.js" "$JIA/frontend/js/"
cp "$ROOT/data/dw/brand_metrics_weekly.csv" "$JIA/data/dw/"
cp "$ROOT/data/dw/bi_mapping.json.example" "$JIA/data/dw/"
cp "$ROOT/data/brands_master.json" "$JIA/data/"
cp "$ROOT/docs/品牌主数据-M6-11品牌.md" "$JIA/docs/"
cp "$ROOT/docs/品牌主数据-v1.md" "$JIA/docs/" 2>/dev/null || true
cp "$ROOT/database/migrate_m6_11_brands.sql" "$JIA/database/" 2>/dev/null || mkdir -p "$JIA/database" && cp "$ROOT/database/migrate_m6_11_brands.sql" "$JIA/database/"
cp "$ROOT/server/seed_m6_brands.py" "$JIA/synced-from-main/server/" 2>/dev/null || mkdir -p "$JIA/synced-from-main/server" && cp "$ROOT/server/seed_m6_brands.py" "$JIA/synced-from-main/server/"
cp "$ROOT/docs/数仓字段口径-v1.md" "$JIA/docs/"
cp "$ROOT/docs/M6并行开发手册-正式版.md" "$JIA/docs/"
cp "$ROOT/docs/发给模块席-M6开包说明.md" "$JIA/docs/"
cp "$ROOT/docs/发给模块席-M6佳璇补发包说明.md" "$JIA/docs/"
cp "$ROOT/docs/M5并行开发手册-正式版.md" "$JIA/docs/" 2>/dev/null || true

cat > "$JIA/PATCHLOG.md" <<EOF
# 佳璇 · M6 开发包（jiaxuan-m6-trial.zip）

> **基线**：jiaxuan-m6-trial-baseline（${STAMP} 补发） · **${BASE_NOTE}**
> **手册**：\`docs/M6并行开发手册-正式版.md\` **V1.3** · §3.2 D-J-M6 · §3.4

## 分工说明（2026-06-30）

**工具包（谈参 / 品牌报告）已由培翛 peixiao-m6-0630 交付并合并主工程。**
佳璇 **不做** \`frontend/toolkit/\` · **勿改** shell 工具包导航。

## 改动清单（仅 D-J-M6）

| # | 交付 | 说明 |
|---|------|------|
| J-1 | 部门–品牌主数据 | ✅ Max 已接：**11 品牌** · \`jc_a\`～\`jc_f\` 真名 · 见 \`docs/品牌主数据-M6-11品牌.md\` |
| J-4 | 档案/数仓 | **11 品牌** profile · 基础建材数仓行（可先空壳） |
| J-5 | FAQ/SLA | 双部门 · **11 品牌**说明 |

## 自测勾选

| 项 | ☐ |
|----|---|
| J-1 品牌映射表齐全 | ☐ |
| J-4 十一品牌档案可开 | ☐ |
| J-5 FAQ/SLA 已更新 | ☐ |
| 未改 toolkit/ · visit · intel | ☐ |

## 发给 Max

- 文件名：\`jiaxuan-m6-trial.zip\`
EOF

cat > "$JIA/README-BASELINE.md" <<EOF
# 佳璇 · M6 开工 baseline（补发 · ${STAMP}）

> **代号** m6-trial · **${BASE_NOTE}**
> **手册 V1.3**：分工已调整 — **谈参/品牌报告归培翛**；J-1 **11 品牌真名 Max 已落主工程**

## 与首版 baseline 的差异

| 项 | 首版 baseline | 本补发包 |
|----|---------------|----------|
| 工具包 | 手册写佳璇做谈参+品牌报告 | **培翛已交付**（见主工程 \`web/toolkit/\`） |
| 品牌 | 5 品牌 | **11 品牌**（KA 5 + 建材 6 · \`data/brands_master.json\` 含 jc_a～f） |
| 合并态 | prod-web-m5-pilot | **+ peixiao-m6-0630 + kaikai-m6-0630** |

## 你的 M6 任务（摘要 · 见手册 D-J-M6）

- **J-1** ✅ 真名已定（Max M6-A）；你补 **BI 映射 + 数仓**
- **J-4** **11 品牌**档案/数仓
- **J-5** FAQ/SLA

**不做**：谈参/品牌报告（培翛）· 拜访导入 · 情报 · 名单

## 开发规则

1. 只改本包 \`frontend/profile.html\` + \`synced-from-main/\` 档案/数仓相关
2. **勿改** \`toolkit/\` · \`visit.html\` · \`intel.html\` · auth/admin
3. 对照 \`synced-from-main/\` 与主工程 API
4. 交包：\`jiaxuan-m6-trial.zip\`

详见 \`docs/发给模块席-M6佳璇补发包说明.md\`
EOF

if [[ -f "$JIA/README.md" ]]; then
  sed -i '' 's/M5 ·/M6 ·/g; s/m5-pilot/m6-trial/g; s/M5 主改/M6 主改/g' "$JIA/README.md" 2>/dev/null || \
    sed -i 's/M5 ·/M6 ·/g; s/m5-pilot/m6-trial/g; s/M5 主改/M6 主改/g' "$JIA/README.md" 2>/dev/null || true
fi

cd "$OUT"
rm -f "jiaxuan-m6-${CODE}-baseline.zip"
zip -r -q "jiaxuan-m6-${CODE}-baseline.zip" "jiaxuan-m6-${CODE}-baseline"
echo "✅ jiaxuan-m6-${CODE}-baseline.zip  ($(du -h "jiaxuan-m6-${CODE}-baseline.zip" | cut -f1))"
