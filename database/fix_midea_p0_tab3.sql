-- Tab3 / P-1 验收：恢复美的 pending P0（外网测试若已 closed 导致 Tab3 空白）
-- 执行一次即可；重复执行安全
USE brand_sandtable;

UPDATE intel_alerts SET status = 'pending'
WHERE brand_id = 1 AND priority = 'P0'
  AND title IN (
    '美的电商总经理岗位变动传闻',
    '抖音618资源倾斜·美的预算外溢',
    '美的全屋智能战略：厨电资源倾斜'
  );

DELETE FROM intel_briefing_cache WHERE brand_id = 1;

SELECT brand_id, priority, category, status, title
FROM intel_alerts
WHERE brand_id = 1 AND priority = 'P0'
ORDER BY id;
