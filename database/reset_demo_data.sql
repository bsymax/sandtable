-- 06-12 联调：清理情报测试脏数据并重灌种子
-- 用法：~/mysql-sandtable/mysql/bin/mysql -u root brand_sandtable < database/reset_demo_data.sql

USE brand_sandtable;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE intel_alerts;
TRUNCATE TABLE intel_briefing_cache;
TRUNCATE TABLE intel_news;
SET FOREIGN_KEY_CHECKS = 1;

-- 新闻种子（10条）
INSERT INTO intel_news (brand_id, title, summary, source, sentiment, category, keywords, published_at) VALUES
(1, '美的电商事业部总经理王建国近期可能岗位变动', '多渠道交叉验证显示王建国可能在Q3调岗。若属实，关键决策链将断裂。', '行业情报', 'negative', '人事', '美的,王建国,岗位变动', '2026-06-07 14:00:00'),
(1, '抖音618家电专场：美的拿下主会场核心资源位', '抖音获家电主会场头图+搜索品牌专区。京东侧仅为品类楼层第三位，品牌预算向抖音倾斜。', '竞对监测', 'negative', '竞品', '抖音,618,美的,资源位', '2026-06-07 10:30:00'),
(2, '九阳K系列抖音月销+45%，JD侧K9 Pro谈判停滞', 'JD库存深度不足，抖音侧热卖而JD缺货/缺价并存。建议48h内推进包销价。', '手工录入', 'negative', '渠道', '九阳,K9 Pro,抖音,618', '2026-06-07 09:15:00'),
(5, '摩飞品牌方运营总监刘洋离职传闻确认中', '猎头渠道显示摩飞正在招聘电商运营总监。建议主动联系确认。', '外部情报', 'negative', '人事', '摩飞,运营总监,离职', '2026-06-06 16:00:00'),
(3, '苏泊尔Q2财报预告：线上渠道增速放缓至5%', '线上全渠道增速放缓。可能影响京东业绩压力与广告预算谈判。', '行业情报', 'neutral', '行业', '苏泊尔,Q2,增速放缓', '2026-06-05 11:00:00'),
(4, '小熊电器618联名款首发预计突破500万', '小熊电器与IP联名款养生壶618首发，预售数据超预期，有望冲击品类第一。', '电商监测', 'positive', '新品', '小熊电器,联名款,618', '2026-06-08 08:00:00'),
(2, '九阳破壁机L18系列京东市占回升至22%', '九阳破壁机L18系列在京东渠道市占率回升，618促销力度加大后效果显著。', '电商监测', 'positive', '渠道', '九阳,破壁机,L18,市占', '2026-06-06 14:00:00'),
(1, '美的全屋智能战略发布：厨电品类将获资源倾斜', '美的集团发布全屋智能新战略，厨小事业部作为核心品类将获得更多研发和营销资源。', '官方渠道', 'positive', '行业', '美的,全屋智能,厨电', '2026-06-05 09:00:00'),
(3, '苏泊尔广告预算缩减信号：主要竞品加大投放', '苏泊尔Q2广告投入环比下降12%，而美的、九阳加大618投放，市占率面临压力。', '竞对监测', 'negative', '竞品', '苏泊尔,广告预算,竞品', '2026-06-04 16:00:00'),
(4, '小熊电器养生壶品类稳居京东第一，领先优势扩大', '小熊电器养生壶京东月GMV突破420万，市占率领先第二名8个百分点。', '电商监测', 'positive', '渠道', '小熊电器,养生壶,市占', '2026-06-03 10:00:00');

-- 周报叙事写入 brand_metrics（与档案经营底表同一行，GMV 以 gmv/gmv_wow 为准）
UPDATE brand_metrics SET week_start='2026-06-02', week_end='2026-06-08', intel_report_status='submitted',
  competitor_moves='苏泊尔加大618投放，九阳K系列抖音热卖', inventory_status='空气炸锅Pro库存偏紧，需补货',
  risk_points='抖音资源倾斜导致预算外溢', opportunities='全屋智能战略带来厨电资源倾斜机会',
  next_week_plan='推进联合投放600万方案确认', reporter='周采销'
WHERE brand_id=1 AND period_value='2026W23';
UPDATE brand_metrics SET week_start='2026-06-02', week_end='2026-06-08', intel_report_status='submitted',
  competitor_moves='美的破壁机促销力度加大', inventory_status='K9 Pro JD侧库存不足',
  risk_points='包销价谈判停滞', opportunities='618专区曝光可争取',
  next_week_plan='锁定618库存与价格', reporter='吴采销'
WHERE brand_id=2 AND period_value='2026W23';
UPDATE brand_metrics SET week_start='2026-06-02', week_end='2026-06-08', intel_report_status='submitted',
  competitor_moves='竞品广告预算缩减', inventory_status='整体库存健康',
  risk_points='线上增速放缓至5%', opportunities='广告置换谈判窗口',
  next_week_plan='Q2复盘拜访准备', reporter='李采销'
WHERE brand_id=3 AND period_value='2026W23';
UPDATE brand_metrics SET week_start='2026-06-02', week_end='2026-06-08', intel_report_status='submitted',
  competitor_moves='养生壶品类竞争加剧', inventory_status='联名款预售超预期',
  risk_points='产能跟进压力', opportunities='618联名款冲击品类第一',
  next_week_plan='协调产能与曝光资源', reporter='王采销'
WHERE brand_id=4 AND period_value='2026W23';
UPDATE brand_metrics SET week_start='2026-06-02', week_end='2026-06-08', intel_report_status='submitted',
  competitor_moves='摩飞人事变动传闻', inventory_status='多功能锅库存充足',
  risk_points='决策链可能变化', opportunities='新品线合作待确认',
  next_week_plan='确认运营总监变动情况', reporter='赵采销'
WHERE brand_id=5 AND period_value='2026W23';

-- 预警种子（6条，含美的 P0 增长机会）
INSERT INTO intel_alerts (brand_id, news_id, priority, category, title, description, suggestion, status) VALUES
(1, 1, 'P0', '风险预警', '美的电商总经理岗位变动传闻', '多渠道交叉验证显示王建国可能在Q3调岗。若属实，关键决策链将断裂，需尽早确认并建立新对接人关系。', '建议本周内拜访确认决策链', 'pending'),
(1, 2, 'P0', '风险预警', '抖音618资源倾斜·美的预算外溢', '抖音获家电主会场头图+搜索品牌专区。京东侧仅为品类楼层第三位，品牌预算向抖音倾斜趋势明显。', '建议48h内与品牌方沟通京东侧资源置换方案', 'pending'),
(1, 8, 'P0', '增长机会', '美的全屋智能战略：厨电资源倾斜', '美的集团发布全屋智能新战略，厨小事业部作为核心品类将获得更多研发和营销资源。', '建议推进京东侧联合营销与新品首发方案', 'pending'),
(2, 3, 'P0', '风险预警', '九阳K系列抖音热销 · JD谈判停滞', 'JD库存深度不足，抖音侧热卖而JD缺货/缺价并存。', '建议48h内推进K9 Pro包销价与618专区库存锁定', 'pending'),
(5, 4, 'P1', '风险预警', '摩飞运营总监离职待确认', '猎头渠道显示摩飞正在招聘电商运营总监。建议主动联系确认并评估对已推进合作的影响。', '补全决策链信息后安排拜访', 'pending'),
(3, 5, 'P1', '增长机会', '苏泊尔Q2线上增速放缓', '线上全渠道增速放缓至5%。可能影响京东业绩压力与广告预算谈判。', '关注广告预算变化，准备应对方案', 'pending');

SELECT 'intel_news' AS tbl, COUNT(*) AS cnt FROM intel_news
UNION ALL SELECT 'brand_metrics_intel', COUNT(*) FROM brand_metrics WHERE intel_report_status IS NOT NULL
UNION ALL SELECT 'intel_alerts', COUNT(*) FROM intel_alerts;

-- 清理联调产生的拜访脏数据（保留 schema 种子 purpose）
UPDATE intel_alerts SET visit_id = NULL
WHERE visit_id IN (
  SELECT id FROM (SELECT v.id FROM visits v
    WHERE v.purpose REGEXP '验收|hpx|跑通|123123|111'
       OR v.purpose LIKE '[预警]%'
       OR v.purpose LIKE '%618后拜访%') AS junk
);

DELETE t FROM todos t
INNER JOIN visits v ON t.visit_id = v.id
WHERE v.purpose REGEXP '验收|hpx|跑通|123123|111'
   OR v.purpose LIKE '[预警]%'
   OR v.purpose LIKE '%618后拜访%';

DELETE c FROM commitments c
INNER JOIN visits v ON c.visit_id = v.id
WHERE v.purpose REGEXP '验收|hpx|跑通|123123|111'
   OR v.purpose LIKE '[预警]%'
   OR v.purpose LIKE '%618后拜访%';

DELETE r FROM visit_records r
INNER JOIN visits v ON r.visit_id = v.id
WHERE v.purpose REGEXP '验收|hpx|跑通|123123|111'
   OR v.purpose LIKE '[预警]%'
   OR v.purpose LIKE '%618后拜访%';

DELETE a FROM visit_attendees a
INNER JOIN visits v ON a.visit_id = v.id
WHERE v.purpose REGEXP '验收|hpx|跑通|123123|111'
   OR v.purpose LIKE '[预警]%'
   OR v.purpose LIKE '%618后拜访%';

DELETE FROM visits
WHERE purpose REGEXP '验收|hpx|跑通|123123|111'
   OR purpose LIKE '[预警]%'
   OR purpose LIKE '%618后拜访%';

-- 清理联调产生的拜访记录脏数据（visit_id=1 的测试纪要「222」）
DELETE FROM todos WHERE record_id = 4 OR visit_id IN (
  SELECT id FROM (SELECT v.id FROM visits v
    INNER JOIN visit_records r ON r.visit_id = v.id
    WHERE r.topics REGEXP '^222$|验收测试') AS x
);
DELETE FROM commitments WHERE record_id = 4;
DELETE FROM visit_records WHERE id = 4 OR topics REGEXP '^222$|验收测试';
UPDATE visits SET record_id = NULL, status = 'scheduled'
WHERE purpose = '618投放+新品';

SELECT 'visits_after_cleanup' AS tbl, COUNT(*) AS cnt FROM visits;
SELECT 'visit_records' AS tbl, COUNT(*) AS cnt FROM visit_records;
