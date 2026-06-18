-- M4-C · 数仓口径 v1.5：销量同比 + 淘宝市占/渠道增速
-- 用法: mysql -u root -p brand_sandtable < database/migrate_m4_metrics_v15.sql

SET NAMES utf8mb4;
USE brand_sandtable;

ALTER TABLE brand_metrics
  ADD COLUMN IF NOT EXISTS sales_volume_yoy DECIMAL(6,2) DEFAULT NULL COMMENT '销量同比%' AFTER sales_volume_wow,
  ADD COLUMN IF NOT EXISTS taobao_share DECIMAL(5,2) DEFAULT NULL COMMENT '淘宝市占%' AFTER douyin_share,
  ADD COLUMN IF NOT EXISTS channel_growth_taobao DECIMAL(5,2) DEFAULT NULL COMMENT '淘宝渠道增速%' AFTER channel_growth_douyin;
