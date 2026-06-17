-- M3 开开 · intel_briefing_cache LLM 摘要列
-- 用法: mysql -u root -p brand_sandtable < database/migrate_m3_intel_llm.sql
-- 本机亦可: cd server && python3 bootstrap_local_db.py

ALTER TABLE intel_briefing_cache
  ADD COLUMN llm_summary TEXT NULL COMMENT 'M3: LLM 简报摘要' AFTER briefing_data;

ALTER TABLE intel_briefing_cache
  ADD COLUMN llm_generated_at DATETIME NULL COMMENT 'M3: LLM 摘要生成时间' AFTER llm_summary;
