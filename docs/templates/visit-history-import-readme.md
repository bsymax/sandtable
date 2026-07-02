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
