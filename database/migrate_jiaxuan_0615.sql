-- M1 补丁 0615 · 佳璇 brand_metrics（Max 合并后执行一次）
-- 1) orders → sales_volume  2) 合并后请再跑: cd server && python3 seed_brand_metrics.py

USE brand_sandtable;

-- 若已是 sales_volume 会报错，可忽略该句
ALTER TABLE brand_metrics
  CHANGE COLUMN orders sales_volume INT DEFAULT NULL COMMENT '销量',
  CHANGE COLUMN orders_wow sales_volume_wow DECIMAL(6,2) DEFAULT NULL COMMENT '销量环比%';
