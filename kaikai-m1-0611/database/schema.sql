-- =============================================
-- 品牌情报平台 · 建表脚本（情报席·开开）
-- 依赖：需要品牌沙盘 brands 表已存在
-- =============================================

-- 品牌主数据（如未创建，请先执行培翛的拜访模块建表脚本）
-- brands 表的 name_key 统一为: midea / joyoung / supor / bear / morphy

-- -----------------------------------------
-- 1. 外部新闻/资讯表
-- -----------------------------------------
DROP TABLE IF EXISTS intel_news;
CREATE TABLE intel_news (
  id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '新闻ID',
  brand_id      INT UNSIGNED    DEFAULT NULL COMMENT '关联品牌ID',
  title         VARCHAR(255)    NOT NULL COMMENT '新闻标题',
  summary       TEXT            DEFAULT NULL COMMENT '新闻摘要',
  url           VARCHAR(512)    DEFAULT NULL COMMENT '原始链接',
  source        VARCHAR(64)     DEFAULT NULL COMMENT '来源',
  sentiment     ENUM('positive','negative','neutral') DEFAULT 'neutral' COMMENT '情感倾向',
  category      VARCHAR(32)     DEFAULT NULL COMMENT '分类',
  keywords      VARCHAR(255)    DEFAULT NULL COMMENT '匹配关键词',
  url_fingerprint CHAR(64)      DEFAULT NULL COMMENT 'URL SHA256去重指纹',
  published_at  DATETIME        DEFAULT NULL COMMENT '发布日期',
  fetched_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '抓取时间',
  created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_news_brand (brand_id),
  INDEX idx_news_sentiment (sentiment),
  INDEX idx_news_published (published_at),
  INDEX idx_news_fingerprint (url_fingerprint),
  FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='外部新闻/资讯表';

-- -----------------------------------------
-- 2. 内部周报表
-- -----------------------------------------
DROP TABLE IF EXISTS intel_weekly_reports;
CREATE TABLE intel_weekly_reports (
  id               INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '周报ID',
  brand_id         INT UNSIGNED    NOT NULL COMMENT '关联品牌ID',
  week_start       DATE           NOT NULL COMMENT '周开始日期',
  week_end         DATE           NOT NULL COMMENT '周结束日期',
  week_label       VARCHAR(16)    DEFAULT NULL COMMENT '周标签',
  weekly_gmv       DECIMAL(12,2)  DEFAULT NULL COMMENT '本周GMV（万元）',
  gmv_change       DECIMAL(6,2)   DEFAULT NULL COMMENT 'GMV环比变化%',
  competitor_moves TEXT           DEFAULT NULL COMMENT '竞品动态',
  inventory_status TEXT           DEFAULT NULL COMMENT '库存状况',
  risk_points      TEXT           DEFAULT NULL COMMENT '风险点',
  opportunities    TEXT           DEFAULT NULL COMMENT '机会点',
  next_week_plan   TEXT           DEFAULT NULL COMMENT '下周计划',
  reporter         VARCHAR(32)    DEFAULT NULL COMMENT '填报人',
  status           ENUM('draft','submitted') DEFAULT 'draft' COMMENT '状态',
  created_at       DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at       DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_brand_week (brand_id, week_start),
  FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='内部周报表';

-- -----------------------------------------
-- 3. 情报预警表
-- -----------------------------------------
DROP TABLE IF EXISTS intel_alerts;
CREATE TABLE intel_alerts (
  id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '预警ID',
  brand_id      INT UNSIGNED    DEFAULT NULL COMMENT '关联品牌ID',
  news_id       INT UNSIGNED    DEFAULT NULL COMMENT '关联新闻ID',
  weekly_id     INT UNSIGNED    DEFAULT NULL COMMENT '关联周报ID',
  visit_id      INT UNSIGNED    DEFAULT NULL COMMENT '关联拜访ID',
  priority      ENUM('P0','P1','P2','P3') NOT NULL DEFAULT 'P2' COMMENT '优先级',
  title         VARCHAR(255)    NOT NULL COMMENT '预警标题',
  description   TEXT            DEFAULT NULL COMMENT '预警详情',
  suggestion    TEXT            DEFAULT NULL COMMENT '建议动作',
  ai_analysis   TEXT            DEFAULT NULL COMMENT 'AI分析结果',
  ai_confidence DECIMAL(3,2)   DEFAULT NULL COMMENT 'AI置信度',
  status        ENUM('pending','confirmed','linked','closed') NOT NULL DEFAULT 'pending',
  assignee      VARCHAR(32)    DEFAULT NULL COMMENT '负责人',
  created_at    DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_alert_brand (brand_id),
  INDEX idx_alert_priority (priority),
  INDEX idx_alert_status (status),
  FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE SET NULL,
  FOREIGN KEY (news_id) REFERENCES intel_news(id) ON DELETE SET NULL,
  FOREIGN KEY (weekly_id) REFERENCES intel_weekly_reports(id) ON DELETE SET NULL,
  FOREIGN KEY (visit_id) REFERENCES visits(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='情报预警表';

-- -----------------------------------------
-- 4. 情报简报缓存表
-- -----------------------------------------
DROP TABLE IF EXISTS intel_briefing_cache;
CREATE TABLE intel_briefing_cache (
  id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  brand_id      INT UNSIGNED    NOT NULL,
  briefing_data JSON           DEFAULT NULL,
  generated_at  DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at    DATETIME       DEFAULT NULL,
  created_at    DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_brand_briefing (brand_id),
  FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='情报简报缓存表';

-- -----------------------------------------
-- 种子数据（≥10条）
-- -----------------------------------------

-- 新闻种子（5条）
INSERT INTO intel_news (brand_id, title, summary, source, sentiment, category, keywords, published_at) VALUES
(1, '美的电商事业部总经理王建国近期可能岗位变动', '多渠道交叉验证显示王建国可能在Q3调岗。若属实，关键决策链将断裂。', '行业情报', 'negative', '人事', '美的,王建国,岗位变动', '2026-06-07 14:00:00'),
(1, '抖音618家电专场：美的拿下主会场核心资源位', '抖音获家电主会场头图+搜索品牌专区。京东侧仅为品类楼层第三位，品牌预算向抖音倾斜。', '竞对监测', 'negative', '竞品', '抖音,618,美的,资源位', '2026-06-07 10:30:00'),
(2, '九阳K系列抖音月销+45%，JD侧K9 Pro谈判停滞', 'JD库存深度不足，抖音侧热卖而JD缺货/缺价并存。建议48h内推进包销价。', '手工录入', 'negative', '渠道', '九阳,K9 Pro,抖音,618', '2026-06-07 09:15:00'),
(5, '摩飞品牌方运营总监刘洋离职传闻确认中', '猎头渠道显示摩飞正在招聘电商运营总监。建议主动联系确认。', '外部情报', 'negative', '人事', '摩飞,运营总监,离职', '2026-06-06 16:00:00'),
(3, '苏泊尔Q2财报预告：线上渠道增速放缓至5%', '线上全渠道增速放缓。可能影响京东业绩压力与广告预算谈判。', '行业情报', 'neutral', '行业', '苏泊尔,Q2,增速放缓', '2026-06-05 11:00:00'),
(4, '小熊电器618联名款首发预计突破500万', '小熊电器与IP联名款养生壶618首发，预售数据超预期，有望冲击品类第一。', '电商监测', 'positive', '新品', '小熊电器,联名款,618', '2026-06-08 08:00:00'),
(2, '九阳破壁机L18系列京东市占回升至22%', '九阳破壁机L18系列在京东渠道市占率回升，618促销力度加大后效果显著。', '电商监测', 'positive', '渠道', '九阳,破壁机,L18,市占', '2026-06-06 14:00:00'),
(1, '美的全屋智能战略发布：厨电品类将获资源倾斜', '美的集团发布全屋智能新战略，厨小事业部作为核心品类将获得更多研发和营销资源。', '官方渠道', 'positive', '行业', '美的,全屋智能,厨电', '2026-06-05 09:00:00'),
(3, '苏泊尔广告预算缩减信号：主要竞品加大投放', '苏泊尔Q2广告投入环比下降12%，而美的、九阳加大618投放，市占率面临压力。', '竞对监测', 'negative', '竞品', '苏泊尔,广告预算,竞品', '2026-06-04 16:00:00'),
(4, '小熊电器养生壶品类稳居京东第一，领先优势扩大', '小熊电器养生壶京东月GMV突破420万，市占率领先第二名8个百分点。', '电商监测', 'positive', '渠道', '小熊电器,养生壶,市占', '2026-06-03 10:00:00');

-- 预警种子（5条）
INSERT INTO intel_alerts (brand_id, news_id, priority, title, description, suggestion, status) VALUES
(1, 1, 'P0', '美的电商总经理岗位变动传闻', '多渠道交叉验证显示王建国可能在Q3调岗。若属实，关键决策链将断裂，需尽早确认并建立新对接人关系。', '建议本周内拜访确认决策链', 'pending'),
(1, 2, 'P0', '抖音618资源倾斜·美的预算外溢', '抖音获家电主会场头图+搜索品牌专区。京东侧仅为品类楼层第三位，品牌预算向抖音倾斜趋势明显。', '建议48h内与品牌方沟通京东侧资源置换方案', 'pending'),
(2, 3, 'P0', '九阳K系列抖音热销 · JD谈判停滞', 'JD库存深度不足，抖音侧热卖而JD缺货/缺价并存。', '建议48h内推进K9 Pro包销价与618专区库存锁定', 'pending'),
(5, 4, 'P1', '摩飞运营总监离职待确认', '猎头渠道显示摩飞正在招聘电商运营总监。建议主动联系确认并评估对已推进合作的影响。', '补全决策链信息后安排拜访', 'pending'),
(3, 5, 'P1', '苏泊尔Q2线上增速放缓', '线上全渠道增速放缓至5%。可能影响京东业绩压力与广告预算谈判。', '关注广告预算变化，准备应对方案', 'pending');
