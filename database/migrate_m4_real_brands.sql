-- M4 方案B · 业务真品牌（保留 id 1～5）
-- 用法: cd server && python3 seed_m4_brands.py

SET NAMES utf8mb4;
USE brand_sandtable;

UPDATE brands SET name='九牧',     name_key='jomoo',     level='S', responsible='周采销' WHERE id=1;
UPDATE brands SET name='箭牌',     name_key='arrow',     level='A', responsible='吴采销' WHERE id=2;
UPDATE brands SET name='恒洁',     name_key='hegii',     level='A', responsible='陈采销' WHERE id=3;
UPDATE brands SET name='潜水艇',   name_key='submarine', level='A', responsible='李采销' WHERE id=4;
UPDATE brands SET name='四季沐歌', name_key='micoe',     level='B', responsible='王采销' WHERE id=5;
