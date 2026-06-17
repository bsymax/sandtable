-- M3-C 数仓 v1 · 同步批次与行级日志
-- 用法: mysql -u root -p brand_sandtable < database/migrate_m3_dw.sql

CREATE TABLE IF NOT EXISTS dw_import_batch (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  batch_key     VARCHAR(36)  NOT NULL UNIQUE COMMENT '批次 UUID',
  source        ENUM('csv','api','manual') NOT NULL DEFAULT 'csv',
  source_name   VARCHAR(255) DEFAULT NULL COMMENT '文件名或 API 标识',
  status        ENUM('running','success','partial','failed') NOT NULL DEFAULT 'running',
  total_rows    INT NOT NULL DEFAULT 0,
  inserted      INT NOT NULL DEFAULT 0,
  updated       INT NOT NULL DEFAULT 0,
  skipped       INT NOT NULL DEFAULT 0,
  failed        INT NOT NULL DEFAULT 0,
  error_summary TEXT DEFAULT NULL,
  started_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  finished_at   DATETIME DEFAULT NULL,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数仓导入批次';

CREATE TABLE IF NOT EXISTS sync_log (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  batch_id      INT NOT NULL,
  brand_id      INT UNSIGNED DEFAULT NULL,
  name_key      VARCHAR(32) DEFAULT NULL,
  period_value  VARCHAR(16) DEFAULT NULL,
  action        ENUM('insert','update','skip','error') NOT NULL,
  message       VARCHAR(512) DEFAULT NULL,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_batch (batch_id),
  KEY idx_brand_period (brand_id, period_value),
  CONSTRAINT fk_sync_batch FOREIGN KEY (batch_id) REFERENCES dw_import_batch(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数仓同步行级日志';
