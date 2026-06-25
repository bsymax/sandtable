-- 九牧 Tab2：误将前端 loading 占位写入 brand_profiles
-- 清空后由规则/LLM 重新生成
UPDATE brand_profiles bp
JOIN brands b ON b.id = bp.brand_id
SET
  bp.competitive_landscape = NULL,
  bp.growth_opportunities = NULL
WHERE b.name_key = 'jomoo'
  AND (
    bp.competitive_landscape LIKE '%正在生成 AI 解读%'
    OR bp.growth_opportunities LIKE '%正在生成 AI 解读%'
  );
