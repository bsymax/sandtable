-- 卫浴 5 品牌 Tab2：清 M2 旧 seed 短文 → 占位 → 前端 buildStrategyFallback 规则
UPDATE brand_profiles bp
JOIN brands b ON b.id = bp.brand_id
SET bp.competitive_landscape = '（待补全竞争格局分析）'
WHERE b.id BETWEEN 1 AND 5
  AND bp.competitive_landscape IN (
    '国内卫浴龙头，JD 市占领先；与箭牌、恒洁在智能马桶/花洒品类直接竞争。',
    '陶瓷卫浴核心品牌，TM/TB 份额较高；与九牧在 JD 智能马桶价格带重叠。',
    '中高端卫浴定位，全渠道布局；DY 增速波动需关注内容电商投入。',
    '五金地漏细分强势；卫浴主品类占比提升中。',
    '太阳能+卫浴延伸品牌，季节性强；DY/TB 占比较高。'
  );

UPDATE brand_profiles bp
JOIN brands b ON b.id = bp.brand_id
SET bp.growth_opportunities = '（待补全增长机会）'
WHERE b.id BETWEEN 1 AND 5
  AND bp.growth_opportunities IN (
    '智能马桶品类可争取 JD 品类日；动销商品数（SPU）结构优化带动成交回升。',
    'JD 市占提升空间大，可谈联合搜索与新品首发。',
    '套餐化 SPU 引入 JD，提升客单与动销商品数宽度。',
    '地漏品类优势可带动卫浴配件组合装上架。',
    '旺季前锁定 JD 热水器/卫浴联合促销资源。'
  );
