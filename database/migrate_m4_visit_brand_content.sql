-- M4 · 历史互动 / 承诺追踪 demo 文案与五品牌卫浴对齐
-- 与 migrate_m4_real_brand_content.sql 同一套旧名→新名映射
-- 用法: mysql -u root -p brand_sandtable < database/migrate_m4_visit_brand_content.sql

SET NAMES utf8mb4;
USE brand_sandtable;

-- 品牌名（槽位 1～5 不变）
-- 美的→九牧  九阳→箭牌  苏泊尔→恒洁  小熊→潜水艇  摩飞→四季沐歌
-- 品类 demo：空气炸锅Pro→智能马桶Pro  空气炸锅→智能马桶  K9 Pro→浴室柜L18  破壁机→浴室柜  厨电→卫浴

UPDATE visits SET purpose = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
  REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(purpose,
    '苏泊尔','恒洁'),'美的','九牧'),'九阳','箭牌'),'小熊','潜水艇'),'摩飞','四季沐歌'),
  '空气炸锅Pro','智能马桶Pro'),'空气炸锅','智能马桶'),'K9 Pro','浴室柜L18'),'破壁机','浴室柜'),'厨电','卫浴');

UPDATE visits SET notes = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
  REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(notes,
    '苏泊尔','恒洁'),'美的','九牧'),'九阳','箭牌'),'小熊','潜水艇'),'摩飞','四季沐歌'),
  '空气炸锅Pro','智能马桶Pro'),'空气炸锅','智能马桶'),'K9 Pro','浴室柜L18'),'破壁机','浴室柜'),'厨电','卫浴')
WHERE notes IS NOT NULL AND notes != '';

UPDATE visit_records SET
  topics = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
    REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(topics,
      '苏泊尔','恒洁'),'美的','九牧'),'九阳','箭牌'),'小熊','潜水艇'),'摩飞','四季沐歌'),
    '空气炸锅Pro','智能马桶Pro'),'空气炸锅','智能马桶'),'K9 Pro','浴室柜L18'),'破壁机','浴室柜'),'厨电','卫浴'),
  commitments_raw = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
    REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(commitments_raw,
      '苏泊尔','恒洁'),'美的','九牧'),'九阳','箭牌'),'小熊','潜水艇'),'摩飞','四季沐歌'),
    '空气炸锅Pro','智能马桶Pro'),'空气炸锅','智能马桶'),'K9 Pro','浴室柜L18'),'破壁机','浴室柜'),'厨电','卫浴'),
  undone_items = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
    REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(undone_items,
      '苏泊尔','恒洁'),'美的','九牧'),'九阳','箭牌'),'小熊','潜水艇'),'摩飞','四季沐歌'),
    '空气炸锅Pro','智能马桶Pro'),'空气炸锅','智能马桶'),'K9 Pro','浴室柜L18'),'破壁机','浴室柜'),'厨电','卫浴')
WHERE undone_items IS NOT NULL AND undone_items != '';

UPDATE commitments SET content = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
  REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(content,
    '苏泊尔','恒洁'),'美的','九牧'),'九阳','箭牌'),'小熊','潜水艇'),'摩飞','四季沐歌'),
  '空气炸锅Pro','智能马桶Pro'),'空气炸锅','智能马桶'),'K9 Pro','浴室柜L18'),'破壁机','浴室柜'),'厨电','卫浴');

UPDATE todos SET title = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
  REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(title,
    '苏泊尔','恒洁'),'美的','九牧'),'九阳','箭牌'),'小熊','潜水艇'),'摩飞','四季沐歌'),
  '空气炸锅Pro','智能马桶Pro'),'空气炸锅','智能马桶'),'K9 Pro','浴室柜L18'),'破壁机','浴室柜'),'厨电','卫浴');
