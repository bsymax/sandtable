-- M4 · 角色治理 + LLM 审计 + 数仓来源扩展
-- 用法: mysql -u root -p brand_sandtable < database/migrate_m4.sql

CREATE TABLE IF NOT EXISTS llm_call_log (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  user_id       INT DEFAULT NULL COMMENT 'users.id，未登录为空',
  username      VARCHAR(64) DEFAULT NULL,
  route         VARCHAR(128) NOT NULL COMMENT '调用来源路由标识',
  status        ENUM('success','fallback','quota','error','disabled') NOT NULL DEFAULT 'success',
  tokens_est    INT DEFAULT NULL COMMENT '粗估 token（字符数/4）',
  latency_ms    INT DEFAULT NULL,
  message       VARCHAR(512) DEFAULT NULL,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_llm_user_day (user_id, created_at),
  KEY idx_llm_route (route),
  KEY idx_llm_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='M4 LLM 调用审计';

-- 扩展数仓批次来源（已有表时执行 MODIFY）
ALTER TABLE dw_import_batch
  MODIFY COLUMN source ENUM('csv','api','manual','bi_csv','dts') NOT NULL DEFAULT 'csv';
