-- M4 方案B · 演示文案与五品牌对齐（档案 positioning / 情报标题）
SET NAMES utf8mb4;
USE brand_sandtable;

UPDATE brand_profiles SET
  founded_year='1990年',
  hq='福建泉州',
  positioning='国内卫浴龙头品牌，智能马桶/花洒/五金全品类；工程+零售+电商多渠道布局，JD 为核心阵地之一。',
  org_structure='{"root":"九牧集团","lead":"电商事业部","nodes":["王建国 · 总经理","李敏 · 渠道","张磊 · 产品"]}'
WHERE brand_id=1;

UPDATE brand_profiles SET
  founded_year='1994年',
  hq='广东佛山',
  positioning='综合性卫浴瓷砖品牌，工程家装与零售并重；智能马桶、浴室柜、瓷砖等品类齐全。',
  org_structure='{"root":"箭牌家居","lead":"电商中心","nodes":["陈志远 · VP","赵雪 · JD渠道","供应链 · 待补"]}'
WHERE brand_id=2;

UPDATE brand_profiles SET
  founded_year='1998年',
  hq='广东佛山',
  positioning='智能卫浴与陶瓷洁具品牌，全卫空间解决方案；注重产品创新与渠道精细化运营。',
  org_structure='{"root":"恒洁卫浴","lead":"电商部","nodes":["刘明 · 总监","渠道 · 待补"]}'
WHERE brand_id=3;

UPDATE brand_profiles SET
  founded_year='2004年',
  hq='北京',
  positioning='地漏/角阀/五金辅材细分龙头，家装辅材高复购品类；线上内容电商与家装渠道双驱动。',
  org_structure='{"root":"潜水艇","lead":"电商部","nodes":["孙悦 · 经理","运营 · 待补"]}'
WHERE brand_id=4;

UPDATE brand_profiles SET
  founded_year='2000年',
  hq='江苏连云港',
  positioning='太阳能与卫浴相关品类品牌，季节性促销明显；工程与零售渠道并行，电商占比提升中。',
  org_structure='{"root":"四季沐歌","lead":"电商中心","nodes":["运营总监 · 待补","JD · 待补"]}'
WHERE brand_id=5;

-- 情报新闻：标题/摘要中的旧 demo 品牌名替换（brand_id 槽位不变）
UPDATE intel_news SET title=REPLACE(title,'美的','九牧'), summary=REPLACE(summary,'美的','九牧'), keywords=REPLACE(keywords,'美的','九牧') WHERE brand_id=1;
UPDATE intel_news SET title=REPLACE(title,'九阳','箭牌'), summary=REPLACE(summary,'九阳','箭牌'), keywords=REPLACE(keywords,'九阳','箭牌') WHERE brand_id=2;
UPDATE intel_news SET title=REPLACE(title,'苏泊尔','恒洁'), summary=REPLACE(summary,'苏泊尔','恒洁'), keywords=REPLACE(keywords,'苏泊尔','恒洁') WHERE brand_id=3;
UPDATE intel_news SET title=REPLACE(title,'小熊','潜水艇'), summary=REPLACE(summary,'小熊','潜水艇'), keywords=REPLACE(keywords,'小熊','潜水艇') WHERE brand_id=4;
UPDATE intel_news SET title=REPLACE(title,'摩飞','四季沐歌'), summary=REPLACE(summary,'摩飞','四季沐歌'), keywords=REPLACE(keywords,'摩飞','四季沐歌') WHERE brand_id=5;

UPDATE intel_alerts SET title=REPLACE(title,'美的','九牧'), description=REPLACE(description,'美的','九牧'), suggestion=REPLACE(suggestion,'美的','九牧') WHERE brand_id=1;
UPDATE intel_alerts SET title=REPLACE(title,'九阳','箭牌'), description=REPLACE(description,'九阳','箭牌'), suggestion=REPLACE(suggestion,'九阳','箭牌') WHERE brand_id=2;
UPDATE intel_alerts SET title=REPLACE(title,'苏泊尔','恒洁'), description=REPLACE(description,'苏泊尔','恒洁'), suggestion=REPLACE(suggestion,'苏泊尔','恒洁') WHERE brand_id=3;
UPDATE intel_alerts SET title=REPLACE(title,'小熊','潜水艇'), description=REPLACE(description,'小熊','潜水艇') WHERE brand_id=4;
UPDATE intel_alerts SET title=REPLACE(title,'摩飞','四季沐歌'), description=REPLACE(description,'摩飞','四季沐歌') WHERE brand_id=5;
