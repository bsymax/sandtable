-- M2 · 佳璇 brand_profiles 字段（Max 合并后执行一次）
-- 若列已存在会报错，可忽略

USE brand_sandtable;

ALTER TABLE brand_profiles
  ADD COLUMN competitive_landscape TEXT NULL COMMENT '竞争格局（M2 可编辑）',
  ADD COLUMN growth_opportunities TEXT NULL COMMENT '增长机会（M2 可编辑）';
