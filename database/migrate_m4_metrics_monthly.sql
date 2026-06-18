-- M4-C · 数仓主频切 monthly：清理 weekly 种子/样例，避免 API 混读
-- 用法: mysql -u root -p brand_sandtable < database/migrate_m4_metrics_monthly.sql
-- 或 bootstrap_local_db.py 自动执行

SET NAMES utf8mb4;
USE brand_sandtable;

DELETE FROM brand_metrics WHERE period_type = 'weekly';

-- 清理旧 weekly 样例 CSV 误导入的 2026-06 monthly 占位（bi_csv 真数截至 2026-05）
DELETE FROM brand_metrics WHERE period_type = 'monthly' AND period_value = '2026-06';
