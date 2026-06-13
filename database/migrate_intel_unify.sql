-- 情报底表统一：周报并入 brand_metrics，预警改 FK metrics_id
-- 用法：cd server && python3 -c "..." 或 mysql < database/migrate_intel_unify.sql

USE brand_sandtable;

-- 1) brand_metrics 扩展字段（已存在则跳过需手动处理重复列报错）
ALTER TABLE brand_metrics
  ADD COLUMN week_start DATE DEFAULT NULL COMMENT '周开始（情报周报）' AFTER ad_rate,
  ADD COLUMN week_end DATE DEFAULT NULL COMMENT '周结束（情报周报）' AFTER week_start,
  ADD COLUMN competitor_moves TEXT DEFAULT NULL COMMENT '竞品动态' AFTER week_end,
  ADD COLUMN inventory_status TEXT DEFAULT NULL COMMENT '库存状况' AFTER competitor_moves,
  ADD COLUMN risk_points TEXT DEFAULT NULL COMMENT '风险点' AFTER inventory_status,
  ADD COLUMN opportunities TEXT DEFAULT NULL COMMENT '机会点' AFTER risk_points,
  ADD COLUMN next_week_plan TEXT DEFAULT NULL COMMENT '下周计划' AFTER opportunities,
  ADD COLUMN reporter VARCHAR(32) DEFAULT NULL COMMENT '填报人' AFTER next_week_plan,
  ADD COLUMN intel_report_status ENUM('draft','submitted') DEFAULT NULL COMMENT '情报周报状态' AFTER reporter;

-- 2) 从 intel_weekly_reports 迁移叙事到 brand_metrics（按品牌+W23）
UPDATE brand_metrics bm
INNER JOIN intel_weekly_reports wr ON wr.brand_id = bm.brand_id
SET bm.week_start = wr.week_start,
    bm.week_end = wr.week_end,
    bm.competitor_moves = wr.competitor_moves,
    bm.inventory_status = wr.inventory_status,
    bm.risk_points = wr.risk_points,
    bm.opportunities = wr.opportunities,
    bm.next_week_plan = wr.next_week_plan,
    bm.reporter = wr.reporter,
    bm.intel_report_status = wr.status
WHERE bm.period_type = 'weekly' AND bm.period_value = '2026W23';

-- 3) intel_alerts：weekly_id → metrics_id
SET FOREIGN_KEY_CHECKS = 0;
ALTER TABLE intel_alerts DROP FOREIGN KEY intel_alerts_ibfk_3;
-- 若 FK 名不同，可先 SHOW CREATE TABLE intel_alerts; 再改

ALTER TABLE intel_alerts ADD COLUMN metrics_id INT UNSIGNED DEFAULT NULL COMMENT '关联 brand_metrics' AFTER news_id;

UPDATE intel_alerts a
INNER JOIN intel_weekly_reports wr ON a.weekly_id = wr.id
INNER JOIN brand_metrics bm ON bm.brand_id = wr.brand_id AND bm.period_type = 'weekly' AND bm.period_value = '2026W23'
SET a.metrics_id = bm.id
WHERE a.weekly_id IS NOT NULL;

ALTER TABLE intel_alerts DROP COLUMN weekly_id;
ALTER TABLE intel_alerts ADD CONSTRAINT fk_alert_metrics FOREIGN KEY (metrics_id) REFERENCES brand_metrics(id) ON DELETE SET NULL;

DROP TABLE IF EXISTS intel_weekly_reports;
SET FOREIGN_KEY_CHECKS = 1;

-- 4) 若无 intel_weekly 历史，直接灌 W23 叙事种子
UPDATE brand_metrics SET week_start='2026-06-02', week_end='2026-06-08', intel_report_status='submitted',
  competitor_moves='苏泊尔加大618投放，九阳K系列抖音热卖', inventory_status='空气炸锅Pro库存偏紧，需补货',
  risk_points='抖音资源倾斜导致预算外溢', opportunities='全屋智能战略带来厨电资源倾斜机会',
  next_week_plan='推进联合投放600万方案确认', reporter='周采销'
WHERE brand_id=1 AND period_value='2026W23' AND intel_report_status IS NULL;

UPDATE brand_metrics SET week_start='2026-06-02', week_end='2026-06-08', intel_report_status='submitted',
  competitor_moves='美的破壁机促销力度加大', inventory_status='K9 Pro JD侧库存不足',
  risk_points='包销价谈判停滞', opportunities='618专区曝光可争取',
  next_week_plan='锁定618库存与价格', reporter='吴采销'
WHERE brand_id=2 AND period_value='2026W23' AND intel_report_status IS NULL;

UPDATE brand_metrics SET week_start='2026-06-02', week_end='2026-06-08', intel_report_status='submitted',
  competitor_moves='竞品广告预算缩减', inventory_status='整体库存健康',
  risk_points='线上增速放缓至5%', opportunities='广告置换谈判窗口',
  next_week_plan='Q2复盘拜访准备', reporter='李采销'
WHERE brand_id=3 AND period_value='2026W23' AND intel_report_status IS NULL;

UPDATE brand_metrics SET week_start='2026-06-02', week_end='2026-06-08', intel_report_status='submitted',
  competitor_moves='养生壶品类竞争加剧', inventory_status='联名款预售超预期',
  risk_points='产能跟进压力', opportunities='618联名款冲击品类第一',
  next_week_plan='协调产能与曝光资源', reporter='王采销'
WHERE brand_id=4 AND period_value='2026W23' AND intel_report_status IS NULL;

UPDATE brand_metrics SET week_start='2026-06-02', week_end='2026-06-08', intel_report_status='submitted',
  competitor_moves='摩飞人事变动传闻', inventory_status='多功能锅库存充足',
  risk_points='决策链可能变化', opportunities='新品线合作待确认',
  next_week_plan='确认运营总监变动情况', reporter='赵采销'
WHERE brand_id=5 AND period_value='2026W23' AND intel_report_status IS NULL;

SELECT 'brand_metrics_intel' AS tbl, COUNT(*) AS cnt FROM brand_metrics WHERE intel_report_status IS NOT NULL;
