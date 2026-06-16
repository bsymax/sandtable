-- M2 生产迁移 · 佳璇 brand_profiles + 情报 briefing 缓存表
-- 已有库执行一次；重复执行若列/表已存在会报错，可忽略对应语句

USE brand_sandtable;

ALTER TABLE brand_profiles
  ADD COLUMN competitive_landscape TEXT NULL COMMENT '竞争格局（M2 可编辑）',
  ADD COLUMN growth_opportunities TEXT NULL COMMENT '增长机会（M2 可编辑）';

CREATE TABLE IF NOT EXISTS intel_briefing_cache (
  id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  brand_id      INT UNSIGNED    NOT NULL,
  briefing_data JSON           DEFAULT NULL,
  generated_at  DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at    DATETIME       DEFAULT NULL,
  created_at    DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_brand_briefing (brand_id),
  FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='情报简报缓存表';
