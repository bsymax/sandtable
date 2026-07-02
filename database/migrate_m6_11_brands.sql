-- M6-A · 11 品牌槽位（基础建材 6 真名 + id=11 新增）
-- 用法: mysql brand_sandtable < database/migrate_m6_11_brands.sql
-- 或: cd server && python3 seed_m6_brands.py

SET NAMES utf8mb4;

UPDATE brands SET name='立邦',   name_key='nippon',  level='B', responsible='待定', status='active' WHERE id=6 OR name_key IN ('jc_a', 'nippon');
UPDATE brands SET name='三棵树', name_key='skshu',   level='B', responsible='待定', status='active' WHERE id=7 OR name_key IN ('jc_b', 'skshu');
UPDATE brands SET name='多乐士', name_key='dulux',   level='B', responsible='待定', status='active' WHERE id=8 OR name_key IN ('jc_c', 'dulux');
UPDATE brands SET name='瓦克',   name_key='wacker',  level='B', responsible='待定', status='active' WHERE id=9 OR name_key IN ('jc_d', 'wacker');
UPDATE brands SET name='雨虹防水', name_key='yuhong', level='B', responsible='待定', status='active' WHERE id=10 OR name_key IN ('jc_e', 'yuhong');

INSERT INTO brands (id, name, name_key, level, responsible, archive_score, relation_temp, baseline_freq, status)
SELECT 11, '嘉宝莉', 'carpoly', 'B', '待定', 0, 50, '季度/次', 'active'
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM brands WHERE id=11 OR name_key='carpoly');
