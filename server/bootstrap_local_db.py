#!/usr/bin/env python3
"""
本机库补丁：补齐 M2/M3 相对旧 schema 的缺列（可重复执行，已有列会跳过）
用法: cd server && python3 bootstrap_local_db.py
"""

from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
import pymysql


def _has_column(cur, table, column):
    cur.execute(f"SHOW COLUMNS FROM {table} LIKE %s", (column,))
    return cur.fetchone() is not None


def main():
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
    )
    cur = conn.cursor()

    if _has_column(cur, "brand_metrics", "orders") and not _has_column(cur, "brand_metrics", "sales_volume"):
        cur.execute(
            "ALTER TABLE brand_metrics CHANGE COLUMN orders sales_volume INT DEFAULT NULL COMMENT '销量'"
        )
        print("OK: brand_metrics.orders -> sales_volume")
    if _has_column(cur, "brand_metrics", "orders_wow") and not _has_column(cur, "brand_metrics", "sales_volume_wow"):
        cur.execute(
            "ALTER TABLE brand_metrics CHANGE COLUMN orders_wow sales_volume_wow DECIMAL(6,2) DEFAULT NULL COMMENT '销量环比%'"
        )
        print("OK: brand_metrics.orders_wow -> sales_volume_wow")

    if not _has_column(cur, "brand_profiles", "competitive_landscape"):
        cur.execute(
            "ALTER TABLE brand_profiles ADD COLUMN competitive_landscape TEXT NULL COMMENT '竞争格局（M2 可编辑）'"
        )
        print("OK: brand_profiles.competitive_landscape")
    if not _has_column(cur, "brand_profiles", "growth_opportunities"):
        cur.execute(
            "ALTER TABLE brand_profiles ADD COLUMN growth_opportunities TEXT NULL COMMENT '增长机会（M2 可编辑）'"
        )
        print("OK: brand_profiles.growth_opportunities")

    if not _has_column(cur, "intel_briefing_cache", "llm_summary"):
        cur.execute(
            "ALTER TABLE intel_briefing_cache ADD COLUMN llm_summary TEXT NULL COMMENT 'M3: LLM 简报摘要' AFTER briefing_data"
        )
        print("OK: intel_briefing_cache.llm_summary")
    if not _has_column(cur, "intel_briefing_cache", "llm_generated_at"):
        cur.execute(
            "ALTER TABLE intel_briefing_cache ADD COLUMN llm_generated_at DATETIME NULL COMMENT 'M3: LLM 摘要生成时间' AFTER llm_summary"
        )
        print("OK: intel_briefing_cache.llm_generated_at")

    cur.execute("SHOW TABLES LIKE 'llm_call_log'")
    if not cur.fetchone():
        cur.execute("""
            CREATE TABLE llm_call_log (
              id INT AUTO_INCREMENT PRIMARY KEY,
              user_id INT DEFAULT NULL,
              username VARCHAR(64) DEFAULT NULL,
              route VARCHAR(128) NOT NULL,
              status ENUM('success','fallback','quota','error','disabled') NOT NULL DEFAULT 'success',
              tokens_est INT DEFAULT NULL,
              latency_ms INT DEFAULT NULL,
              message VARCHAR(512) DEFAULT NULL,
              created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
              KEY idx_llm_user_day (user_id, created_at),
              KEY idx_llm_route (route)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='M4 LLM 调用审计'
        """)
        print("OK: llm_call_log 表已创建")

    for col, ddl in (
        ("sales_volume_yoy", "DECIMAL(6,2) DEFAULT NULL COMMENT '销量同比%'"),
        ("taobao_share", "DECIMAL(5,2) DEFAULT NULL COMMENT '淘宝市占%'"),
        ("channel_growth_taobao", "DECIMAL(5,2) DEFAULT NULL COMMENT '淘宝渠道增速%'"),
    ):
        if not _has_column(cur, "brand_metrics", col):
            cur.execute(f"ALTER TABLE brand_metrics ADD COLUMN {col} {ddl}")
            print(f"OK: brand_metrics.{col}")

    try:
        cur.execute(
            "ALTER TABLE dw_import_batch MODIFY COLUMN source "
            "ENUM('csv','api','manual','bi_csv','dts') NOT NULL DEFAULT 'csv'"
        )
        print("OK: dw_import_batch.source 扩展 bi_csv/dts")
    except Exception as exc:
        print(f"skip dw_import_batch.source: {exc}")

    cur.execute("DELETE FROM brand_metrics WHERE period_type = 'weekly'")
    if cur.rowcount:
        print(f"OK: 已清理 weekly 种子 {cur.rowcount} 行")

    cur.execute("DELETE FROM brand_metrics WHERE period_type = 'monthly' AND period_value = '2026-06'")
    if cur.rowcount:
        print(f"OK: 已清理 monthly 2026-06 占位 {cur.rowcount} 行")

    conn.commit()
    conn.close()
    print("bootstrap_local_db 完成")


if __name__ == "__main__":
    main()
