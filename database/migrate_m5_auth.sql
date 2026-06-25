-- M5-A 账号体系：改密/重置 · bcrypt · 首次登录强制改密 · 部门展示
-- 用法: mysql -u brand_app -p brand_sandtable < database/migrate_m5_auth.sql
-- 本机可重复执行: cd server && python3 bootstrap_local_db.py

ALTER TABLE users
  ADD COLUMN must_change_password TINYINT(1) NOT NULL DEFAULT 0 COMMENT '首次/重置后强制改密' AFTER is_active;

ALTER TABLE users
  ADD COLUMN password_algo ENUM('sha256','bcrypt') NOT NULL DEFAULT 'sha256' COMMENT '密码哈希算法' AFTER password_hash;

ALTER TABLE users
  ADD COLUMN dept VARCHAR(128) NULL COMMENT '部门展示（C9）' AFTER display_name;

ALTER TABLE users
  ADD COLUMN last_login_at DATETIME NULL COMMENT '最近登录' AFTER updated_at;

-- 既有演示账号：首次登录强制改密（外网加固）
UPDATE users SET must_change_password = 1 WHERE password_algo = 'sha256';
