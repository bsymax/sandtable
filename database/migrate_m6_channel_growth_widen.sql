-- M6 · 渠道增速列扩宽（建材真数同比可达数千 %）
-- DECIMAL(5,2) 上限 999.99 → seed 导入 1264 Out of range
-- 用法: mysql sandtable < database/migrate_m6_channel_growth_widen.sql

ALTER TABLE brand_metrics
  MODIFY COLUMN channel_growth_jd     DECIMAL(8,2) DEFAULT NULL,
  MODIFY COLUMN channel_growth_tmall  DECIMAL(8,2) DEFAULT NULL,
  MODIFY COLUMN channel_growth_douyin DECIMAL(8,2) DEFAULT NULL,
  MODIFY COLUMN channel_growth_taobao DECIMAL(8,2) DEFAULT NULL COMMENT '淘宝渠道增速%';
