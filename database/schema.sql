-- =============================================
-- 品牌沙盘 M1 · 数据库建表脚本
-- 数据库：brand_sandtable
-- 编码：utf8mb4
-- =============================================

-- 强制会话字符集为 utf8mb4，避免客户端默认 latin1 导致中文乱码
SET NAMES utf8mb4;

-- 关闭外键检查，保证脚本可重复执行（DROP TABLE 不受外键顺序限制）
SET FOREIGN_KEY_CHECKS = 0;

CREATE DATABASE IF NOT EXISTS brand_sandtable
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE brand_sandtable;

-- -----------------------------------------
-- 1. 品牌表
-- -----------------------------------------
DROP TABLE IF EXISTS brands;
CREATE TABLE brands (
  id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '品牌ID',
  name        VARCHAR(64)    NOT NULL COMMENT '品牌名称',
  name_key    VARCHAR(32)    NOT NULL UNIQUE COMMENT '品牌英文标识（midea/joyoung/supor/bear/morphy）',
  level       ENUM('S','A','B','C') NOT NULL DEFAULT 'B' COMMENT '品牌分级（S:战略 A:核心 B:成长 C:观察）',
  responsible VARCHAR(32)    DEFAULT NULL COMMENT '负责采销',
  archive_score INT          DEFAULT 0 COMMENT '档案完整度评分 0-100',
  relation_temp INT          DEFAULT 50 COMMENT '关系温度 0-100',
  baseline_freq VARCHAR(32)  DEFAULT '季度/次' COMMENT '拜访基线频率',
  status      ENUM('active','inactive') NOT NULL DEFAULT 'active',
  created_at  DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='品牌主数据表';

-- -----------------------------------------
-- 2. 品牌联系人表
-- -----------------------------------------
DROP TABLE IF EXISTS brand_contacts;
CREATE TABLE brand_contacts (
  id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  brand_id    INT UNSIGNED   NOT NULL COMMENT '所属品牌ID',
  name        VARCHAR(32)    NOT NULL COMMENT '联系人姓名',
  title       VARCHAR(64)    DEFAULT NULL COMMENT '职务/角色',
  role_tag    ENUM('决策者','日常对接','需加强','其他') DEFAULT '日常对接' COMMENT '角色标签',
  phone       VARCHAR(20)    DEFAULT NULL,
  wechat      VARCHAR(32)    DEFAULT NULL,
  last_contact_date DATE     DEFAULT NULL COMMENT '最近建联日期',
  is_active   TINYINT(1)     NOT NULL DEFAULT 1,
  created_at  DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='品牌联系人表';

-- -----------------------------------------
-- 3. 拜访安排表
-- -----------------------------------------
DROP TABLE IF EXISTS visits;
CREATE TABLE visits (
  id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  brand_id    INT UNSIGNED   NOT NULL COMMENT '拜访品牌ID',
  visit_date  DATE           NOT NULL COMMENT '拜访日期',
  visit_time  TIME           DEFAULT '14:00:00' COMMENT '拜访时间',
  visit_type  ENUM('urgent','regular','renewal') NOT NULL DEFAULT 'regular' COMMENT '拜访类型',
  purpose     TEXT           NOT NULL COMMENT '拜访目的',
  notes       TEXT           DEFAULT NULL COMMENT '备注',
  status      ENUM('scheduled','completed','cancelled') NOT NULL DEFAULT 'scheduled' COMMENT '拜访状态',
  record_id   INT UNSIGNED   DEFAULT NULL COMMENT '关联拜访记录ID',
  created_at  DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='拜访安排表';

-- -----------------------------------------
-- 4. 拜访参与人员关联表（多对多）
-- -----------------------------------------
DROP TABLE IF EXISTS visit_attendees;
CREATE TABLE visit_attendees (
  id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  visit_id    INT UNSIGNED   NOT NULL COMMENT '拜访ID',
  contact_id  INT UNSIGNED   DEFAULT NULL COMMENT '品牌联系人ID（可选）',
  name        VARCHAR(32)    NOT NULL COMMENT '参与人员姓名',
  role        VARCHAR(16)    DEFAULT 'bd' COMMENT '我方/对方：bd=采销方，brand=品牌方',
  created_at  DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (visit_id) REFERENCES visits(id) ON DELETE CASCADE,
  FOREIGN KEY (contact_id) REFERENCES brand_contacts(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='拜访参与人员表';

-- -----------------------------------------
-- 5. 拜访后记录表
-- -----------------------------------------
DROP TABLE IF EXISTS visit_records;
CREATE TABLE visit_records (
  id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  visit_id        INT UNSIGNED   UNIQUE NOT NULL COMMENT '关联拜访ID（一对一）',
  participants    TEXT           DEFAULT NULL COMMENT '参与人员描述',
  topics          TEXT           DEFAULT NULL COMMENT '会谈议题',
  commitments_raw TEXT           DEFAULT NULL COMMENT '原始承诺文本（用于AI抽取）',
  undone_items    TEXT           DEFAULT NULL COMMENT '未达成事项',
  relation_change ENUM('up','flat','down') DEFAULT 'flat' COMMENT '关系温度变化',
  next_visit_date DATE           DEFAULT NULL COMMENT '建议下次拜访日期',
  created_at      DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (visit_id) REFERENCES visits(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='拜访后记录表';

-- -----------------------------------------
-- 6. 承诺事项表
-- -----------------------------------------
DROP TABLE IF EXISTS commitments;
CREATE TABLE commitments (
  id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  visit_id      INT UNSIGNED   NOT NULL COMMENT '关联拜访ID',
  record_id     INT UNSIGNED   DEFAULT NULL COMMENT '关联拜访记录ID',
  content       VARCHAR(255)   NOT NULL COMMENT '承诺内容',
  party         ENUM('brand','bd') DEFAULT 'brand' COMMENT '承诺方：brand=品牌方，bd=采销方',
  status        ENUM('pending','fulfilled','broken') NOT NULL DEFAULT 'pending' COMMENT '状态',
  deadline      DATE           DEFAULT NULL COMMENT '承诺截止日期',
  fulfilled_at  DATETIME       DEFAULT NULL COMMENT '兑现时间',
  created_at    DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (visit_id) REFERENCES visits(id) ON DELETE CASCADE,
  FOREIGN KEY (record_id) REFERENCES visit_records(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='承诺事项表';

-- -----------------------------------------
-- 7. 待办事项表
-- -----------------------------------------
DROP TABLE IF EXISTS todos;
CREATE TABLE todos (
  id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  record_id     INT UNSIGNED   DEFAULT NULL COMMENT '来源拜访记录ID',
  visit_id      INT UNSIGNED   DEFAULT NULL COMMENT '关联拜访ID',
  priority      ENUM('P0','P1','P2','P3') NOT NULL DEFAULT 'P2' COMMENT '优先级',
  title         VARCHAR(255)   NOT NULL COMMENT '待办标题',
  deadline      DATE           DEFAULT NULL COMMENT '截止日期',
  assignee      VARCHAR(32)    DEFAULT NULL COMMENT '负责人',
  status        ENUM('pending','done','overdue') NOT NULL DEFAULT 'pending' COMMENT '状态',
  created_at    DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at  DATETIME       DEFAULT NULL,
  FOREIGN KEY (visit_id) REFERENCES visits(id) ON DELETE SET NULL,
  FOREIGN KEY (record_id) REFERENCES visit_records(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='待办事项表';

-- -----------------------------------------
-- 初始种子数据
-- -----------------------------------------

-- 品牌数据
INSERT INTO brands (name, name_key, level, responsible, archive_score, relation_temp, baseline_freq) VALUES
('九牧',     'jomoo',     'S', '周采销', 88, 72, '2-4周/次'),
('箭牌',     'arrow',     'A', '吴采销', 85, 85, '季度/次'),
('恒洁',     'hegii',     'A', '陈采销', 78, 68, '季度/次'),
('潜水艇',   'submarine', 'A', '李采销', 81, 88, '季度/次'),
('四季沐歌', 'micoe',     'B', '王采销', 71, 65, '季度/次');

-- 联系人数据
INSERT INTO brand_contacts (brand_id, name, title, role_tag, last_contact_date) VALUES
(1, '王建国', '电商事业部总经理', '决策者',   '2026-06-05'),
(1, '李敏',   '京东渠道运营总监', '日常对接', '2026-06-05'),
(1, '张磊',   '产品总监',         '需加强',   '2026-05-15'),
(2, '陈志远', '电商VP',           '决策者',   '2026-05-20'),
(2, '赵雪',   '京东渠道经理',     '日常对接', '2026-05-28'),
(3, '刘明',   '电商总监',         '决策者',   '2026-04-25'),
(4, '孙悦',   '电商经理',         '日常对接', '2026-06-01');

-- 拜访数据
INSERT INTO visits (brand_id, visit_date, visit_time, visit_type, purpose, status) VALUES
(1, '2026-06-10', '14:00:00', 'urgent',  '618投放+新品',            'scheduled'),
(1, '2026-06-05', '10:00:00', 'regular', '季度对齐',                'completed'),
(2, '2026-05-20', '15:00:00', 'regular', '季度复盘',                'completed'),
(2, '2026-06-18', '14:00:00', 'regular', '例行拜访',                'scheduled'),
(3, '2026-06-25', '10:00:00', 'regular', 'Q2复盘+广告置换',          'scheduled'),
(1, '2026-05-15', '10:00:00', 'regular', '产品沟通 · 智能马桶Pro', 'completed');

-- 拜访参与人员
INSERT INTO visit_attendees (visit_id, contact_id, name, role) VALUES
(1, 1, '王建国', 'brand'),
(1, 2, '李敏',   'brand'),
(2, 1, '王建国', 'brand'),
(2, 2, '李敏',   'brand'),
(3, 4, '陈志远', 'brand'),
(3, 5, '赵雪',   'brand');

-- 拜访记录
INSERT INTO visit_records (visit_id, participants, topics, commitments_raw, undone_items, relation_change, next_visit_date) VALUES
(2, '周采销；王建国、李敏',
   '618目标+新品首发',
   '- 3款新品JD首发\n- 联合投放预算600万\n- 智能马桶Pro排期确认',
   NULL,
   'flat', '2026-06-24'),

(3, '吴采销；陈志远、赵雪',
   '浴室柜L18合作沟通',
   '- 浴室柜L18包销价确认\n- 618库存锁定',
   NULL,
   'up', '2026-07-10'),

(6, '周采销；张磊',
   '智能马桶Pro产品沟通',
   '- 1款智能马桶JD首发',
   '仅沟通未签署',
   'flat', '2026-05-30');

-- 更新 visits 中的 record_id 关联
UPDATE visits SET record_id = 1 WHERE id = 2;
UPDATE visits SET record_id = 2 WHERE id = 3;
UPDATE visits SET record_id = 3 WHERE id = 6;

-- 承诺数据
INSERT INTO commitments (visit_id, record_id, content, party, status, deadline) VALUES
(2, 1, '3款新品JD首发',               'brand', 'broken',    '2026-05-30'),
(2, 1, '联合投放预算600万',            'brand', 'pending',   '2026-06-12'),
(2, 1, '智能马桶Pro排期确认',          'brand', 'pending',   '2026-06-15'),
(3, 2, '浴室柜L18包销价确认',             'brand', 'fulfilled', '2026-06-01'),
(3, 2, '618库存锁定',                  'brand', 'pending',   '2026-06-10'),
(6, 3, '1款智能马桶JD首发',            'brand', 'fulfilled', '2026-05-30');

-- 待办数据
INSERT INTO todos (record_id, visit_id, priority, title, deadline, assignee, status) VALUES
(1, 2, 'P0', '跟进600万投放方案确认',       '2026-06-12', '周采销', 'pending'),
(1, 2, 'P0', '跟进智能马桶Pro排期确认',     '2026-06-15', '周采销', 'pending'),
(1, 2, 'P1', '确认王建国岗位变动情况',       '2026-06-20', '周采销', 'pending'),
(1, 2, 'P2', '6/24下次拜访准备',           '2026-06-22', '周采销', 'pending'),
(2, 3, 'P1', '跟进浴室柜L18包销价',           '2026-06-05', '吴采销', 'done'),
(2, 3, 'P2', '618库存方案确认',            '2026-06-10', '吴采销', 'pending');

-- =============================================
-- 品牌档案模块（佳璇，2026-06-11 合并）
-- =============================================

-- -----------------------------------------
-- 8. 品牌档案简介表
-- -----------------------------------------
DROP TABLE IF EXISTS brand_metrics;
DROP TABLE IF EXISTS brand_profiles;
CREATE TABLE brand_profiles (
  id               INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  brand_id         INT UNSIGNED   NOT NULL COMMENT '所属品牌ID',
  founded_year     VARCHAR(16)    DEFAULT NULL COMMENT '成立时间',
  hq               VARCHAR(64)    DEFAULT NULL COMMENT '总部',
  positioning      VARCHAR(255)   DEFAULT NULL COMMENT '品牌定位',
  org_structure    TEXT           DEFAULT NULL COMMENT '组织架构（JSON文本）',
  taboos           TEXT           DEFAULT NULL COMMENT '品牌潜规则',
  competitive_landscape TEXT      DEFAULT NULL COMMENT '竞争格局（M2 可编辑）',
  growth_opportunities  TEXT      DEFAULT NULL COMMENT '增长机会（M2 可编辑）',
  taboo_updated_by VARCHAR(32)    DEFAULT NULL COMMENT '潜规则最后更新人',
  taboo_updated_at DATETIME       DEFAULT NULL COMMENT '潜规则最后更新时间',
  created_at       DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at       DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='品牌档案简介表';

-- -----------------------------------------
-- 9. 品牌经营指标表
-- -----------------------------------------
CREATE TABLE brand_metrics (
  id                    INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  brand_id              INT UNSIGNED   NOT NULL COMMENT '所属品牌ID',
  period_type           ENUM('weekly','monthly') NOT NULL DEFAULT 'weekly',
  period_value          VARCHAR(16)    NOT NULL COMMENT '周期标识，如 2026W23',
  gmv                   DECIMAL(12,2)  DEFAULT NULL COMMENT 'GMV（万元）',
  gmv_wow               DECIMAL(6,2)   DEFAULT NULL COMMENT '周环比%',
  gmv_yoy               DECIMAL(6,2)   DEFAULT NULL COMMENT '同比%',
  sales_volume          INT            DEFAULT NULL COMMENT '销量',
  sales_volume_wow      DECIMAL(6,2)   DEFAULT NULL COMMENT '销量环比%',
  jd_share              DECIMAL(5,2)   DEFAULT NULL COMMENT 'JD市占%',
  jd_share_wow          DECIMAL(5,2)   DEFAULT NULL COMMENT '市占环比变化pp',
  tmall_share           DECIMAL(5,2)   DEFAULT NULL,
  douyin_share          DECIMAL(5,2)   DEFAULT NULL,
  pdd_share             DECIMAL(5,2)   DEFAULT NULL,
  channel_growth_jd     DECIMAL(5,2)   DEFAULT NULL,
  channel_growth_tmall  DECIMAL(5,2)   DEFAULT NULL,
  channel_growth_douyin DECIMAL(5,2)   DEFAULT NULL,
  category_distribution TEXT           DEFAULT NULL COMMENT '三级类目GMV占比 JSON',
  category_share        TEXT           DEFAULT NULL COMMENT '各类目JD市占 JSON',
  sku_count             INT            DEFAULT NULL,
  p0_gap_count          INT            DEFAULT NULL,
  gross_margin          DECIMAL(5,2)   DEFAULT NULL COMMENT '毛利率%',
  uv_conversion         DECIMAL(5,2)   DEFAULT NULL COMMENT 'UV转化率%',
  ad_rate               DECIMAL(5,2)   DEFAULT NULL COMMENT '广告费率%',
  week_start            DATE           DEFAULT NULL COMMENT '周开始（情报周报）',
  week_end              DATE           DEFAULT NULL COMMENT '周结束（情报周报）',
  competitor_moves      TEXT           DEFAULT NULL COMMENT '竞品动态（情报叙事）',
  inventory_status      TEXT           DEFAULT NULL COMMENT '库存状况（情报叙事）',
  risk_points           TEXT           DEFAULT NULL COMMENT '风险点（情报叙事）',
  opportunities         TEXT           DEFAULT NULL COMMENT '机会点（情报叙事）',
  next_week_plan        TEXT           DEFAULT NULL COMMENT '下周计划（情报叙事）',
  reporter              VARCHAR(32)    DEFAULT NULL COMMENT '填报人（情报周报）',
  intel_report_status   ENUM('draft','submitted') DEFAULT NULL COMMENT '情报周报状态',
  created_at            DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at            DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_brand_period (brand_id, period_type, period_value),
  FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='品牌经营指标快照表（档案看板+情报周报共用）';

-- 品牌档案种子数据
INSERT INTO brand_profiles (brand_id, founded_year, hq, positioning, org_structure, taboos, taboo_updated_by, taboo_updated_at) VALUES
(1, '1968年', '广东佛山顺德', '全球化科技集团，智能家居与全品类家电龙头；多品牌矩阵（美的/COLMO/东芝等），全渠道+DTC转型中。',
 '{"root":"美的集团","lead":"电商事业部","nodes":["王建国 · 总经理","李敏 · 渠道","张磊 · 产品"]}',
 '王总不喜欢饭局谈正事，建议工作日早上10点前约短会。\n合同谈判偏好：先邮件沟通条款，再面谈拍板。',
 '周采销', '2026-05-20 10:00:00'),
(2, '1994年', '山东济南', '原创创新与健康生活方式的品质小家电品牌；豆浆机起家，破壁机/电饭煲/空气炸锅等厨电全品类布局。',
 '{"root":"九阳股份","lead":"电商中心","nodes":["陈志远 · VP","赵雪 · JD渠道","供应链 · 待补"]}',
 'VP层级会议需提前3天邮件预约，附带JD数据简报。',
 '吴采销', '2026-03-12 09:00:00'),
(3, '1994年', '浙江杭州（制造基地玉环）', '中国炊具与小家电行业领跑者，SEB集团旗下；明火炊具+厨房小家电+生活家居多品类，注重ROI与品牌矩阵。',
 '{"root":"苏泊尔集团","lead":"电商部","nodes":["刘明 · 总监","京东组 · 待补"]}',
 '品牌方当前更关注ROI，大规模要量易被拒，建议带数据方案。',
 '陈采销', '2026-02-18 14:00:00'),
(4, '2006年', '广东佛山顺德', '「年轻人喜欢的小家电」——创意小电品牌，养生壶/电饭煲mini等细分品类领先，线上渠道优势明显。',
 '{"root":"小熊电器","lead":"电商部","nodes":["孙悦 · 电商经理","市场 · 联名"]}',
 '品牌方对联名款创意敏感，需带视觉草案再谈，避免空口承诺。',
 '李采销', '2026-05-18 11:00:00'),
(5, '1936年', '英国品牌 / 中国运营：广东佛山', '英伦高端创意小电，1936年英国创立；2013年由新宝股份引入中国，抖音/小红书内容电商强势，JD渠道待深化。',
 '{"root":"新宝股份","lead":"摩飞品牌事业部","nodes":["总监 · 待补","私域 · 待补","产品 · 待补"]}',
 '（待补全）决策人偏好与拜访禁忌尚未录入。',
 NULL, NULL);

-- 品牌经营指标种子数据（当前周 2026W23；近 12 周历史由 server 启动时按
-- jiaxuan seed 规则补全，或运行 jiaxuan-m1-0610/backend/seed.py）
INSERT INTO brand_metrics (
  brand_id, period_type, period_value, gmv, gmv_wow, gmv_yoy, sales_volume, sales_volume_wow,
  jd_share, jd_share_wow, tmall_share, douyin_share, pdd_share,
  channel_growth_jd, channel_growth_tmall, channel_growth_douyin,
  category_distribution, category_share, sku_count, p0_gap_count,
  gross_margin, uv_conversion, ad_rate
) VALUES
(1, 'weekly', '2026W23', 487.00, -16.30, -8.10, 48200, -12.00,
 31.20, -2.10, 24.80, 28.50, 8.20, -16.30, -5.20, 22.00,
 '[{"name":"空气炸锅","share":22},{"name":"电饭煲","share":17},{"name":"破壁机","share":12},{"name":"电热水壶","share":9},{"name":"微波炉","share":7}]',
 '[{"name":"空气炸锅","jd_share":28,"avg":22},{"name":"电饭煲","jd_share":31,"avg":24},{"name":"破壁机","jd_share":18,"avg":20}]',
 428, 3, 22.40, 4.20, 5.00),
(2, 'weekly', '2026W23', 512.00, 12.10, 6.20, 22800, 4.50,
 18.50, 0.80, 28.00, 32.00, 12.00, 3.20, 2.10, 45.00,
 '[{"name":"破壁机","share":24},{"name":"豆浆机","share":18},{"name":"电饭煲","share":15},{"name":"养生壶","share":12}]',
 '[{"name":"破壁机","jd_share":22,"avg":20},{"name":"豆浆机","jd_share":25,"avg":21}]',
 186, 2, 26.80, 5.10, 3.80),
(3, 'weekly', '2026W23', 623.00, -5.20, 4.20, 16500, 3.80,
 14.20, -1.50, 32.00, 22.00, 14.00, 5.00, 3.00, 8.00,
 '[{"name":"电饭煲","share":28},{"name":"破壁机","share":20},{"name":"炒锅","share":15}]',
 '[{"name":"电饭煲","jd_share":16,"avg":22},{"name":"破壁机","jd_share":14,"avg":20}]',
 152, 1, 24.10, 4.60, 7.50),
(4, 'weekly', '2026W23', 298.00, 32.00, 18.00, 11200, 18.00,
 38.00, 3.50, 22.00, 28.00, 8.00, 15.00, 8.00, 35.00,
 '[{"name":"养生壶","share":33},{"name":"电饭煲mini","share":24},{"name":"空气炸锅","share":22}]',
 '[{"name":"养生壶","jd_share":42,"avg":18},{"name":"电饭煲mini","jd_share":35,"avg":15}]',
 96, 0, 28.50, 5.80, 3.20),
(5, 'weekly', '2026W23', 187.00, 3.50, 10.00, 6800, 6.00,
 18.50, 0.50, 20.00, 45.00, 10.00, 8.00, 5.00, 38.00,
 '[{"name":"多功能锅","share":35},{"name":"榨汁机","share":22},{"name":"电水壶","share":15}]',
 '[{"name":"多功能锅","jd_share":12,"avg":22},{"name":"榨汁机","jd_share":10,"avg":18}]',
 64, 4, 32.10, 3.80, 2.10);

-- 情报周报叙事字段（写入 brand_metrics，与档案 2026W23 快照同一行）
UPDATE brand_metrics SET week_start='2026-06-02', week_end='2026-06-08', intel_report_status='submitted',
  competitor_moves='苏泊尔加大618投放，九阳K系列抖音热卖', inventory_status='空气炸锅Pro库存偏紧，需补货',
  risk_points='抖音资源倾斜导致预算外溢', opportunities='全屋智能战略带来厨电资源倾斜机会',
  next_week_plan='推进联合投放600万方案确认', reporter='周采销'
WHERE brand_id=1 AND period_value='2026W23';
UPDATE brand_metrics SET week_start='2026-06-02', week_end='2026-06-08', intel_report_status='submitted',
  competitor_moves='美的破壁机促销力度加大', inventory_status='K9 Pro JD侧库存不足',
  risk_points='包销价谈判停滞', opportunities='618专区曝光可争取',
  next_week_plan='锁定618库存与价格', reporter='吴采销'
WHERE brand_id=2 AND period_value='2026W23';
UPDATE brand_metrics SET week_start='2026-06-02', week_end='2026-06-08', intel_report_status='submitted',
  competitor_moves='竞品广告预算缩减', inventory_status='整体库存健康',
  risk_points='线上增速放缓至5%', opportunities='广告置换谈判窗口',
  next_week_plan='Q2复盘拜访准备', reporter='李采销'
WHERE brand_id=3 AND period_value='2026W23';
UPDATE brand_metrics SET week_start='2026-06-02', week_end='2026-06-08', intel_report_status='submitted',
  competitor_moves='养生壶品类竞争加剧', inventory_status='联名款预售超预期',
  risk_points='产能跟进压力', opportunities='618联名款冲击品类第一',
  next_week_plan='协调产能与曝光资源', reporter='王采销'
WHERE brand_id=4 AND period_value='2026W23';
UPDATE brand_metrics SET week_start='2026-06-02', week_end='2026-06-08', intel_report_status='submitted',
  competitor_moves='摩飞人事变动传闻', inventory_status='多功能锅库存充足',
  risk_points='决策链可能变化', opportunities='新品线合作待确认',
  next_week_plan='确认运营总监变动情况', reporter='赵采销'
WHERE brand_id=5 AND period_value='2026W23';

-- =============================================
-- 情报模块（开开，2026-06-11 合并）
-- =============================================

-- -----------------------------------------
-- 10. 外部新闻/资讯表
-- -----------------------------------------
DROP TABLE IF EXISTS intel_briefing_cache;
DROP TABLE IF EXISTS intel_alerts;
DROP TABLE IF EXISTS intel_weekly_reports;
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='外部新闻/资讯表（FK brands）';

-- -----------------------------------------
-- 11. 情报预警表（FK brands / intel_news / brand_metrics / visits）
-- -----------------------------------------
CREATE TABLE intel_alerts (
  id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '预警ID',
  brand_id      INT UNSIGNED    DEFAULT NULL COMMENT '关联品牌ID',
  news_id       INT UNSIGNED    DEFAULT NULL COMMENT '关联新闻ID',
  metrics_id    INT UNSIGNED    DEFAULT NULL COMMENT '关联 brand_metrics 周报周期',
  visit_id      INT UNSIGNED    DEFAULT NULL COMMENT '关联拜访ID',
  priority      ENUM('P0','P1','P2','P3') NOT NULL DEFAULT 'P2' COMMENT '优先级',
  category      ENUM('增长机会','风险预警') DEFAULT NULL COMMENT '情报分类',
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
  FOREIGN KEY (metrics_id) REFERENCES brand_metrics(id) ON DELETE SET NULL,
  FOREIGN KEY (visit_id) REFERENCES visits(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='情报预警表';

-- -----------------------------------------
-- 13. 情报简报缓存表
-- -----------------------------------------
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

-- 新闻种子（10条）
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

-- 预警种子（6条，含美的 P0 增长机会）
INSERT INTO intel_alerts (brand_id, news_id, priority, category, title, description, suggestion, status) VALUES
(1, 1, 'P0', '风险预警', '美的电商总经理岗位变动传闻', '多渠道交叉验证显示王建国可能在Q3调岗。若属实，关键决策链将断裂，需尽早确认并建立新对接人关系。', '建议本周内拜访确认决策链', 'pending'),
(1, 2, 'P0', '风险预警', '抖音618资源倾斜·美的预算外溢', '抖音获家电主会场头图+搜索品牌专区。京东侧仅为品类楼层第三位，品牌预算向抖音倾斜趋势明显。', '建议48h内与品牌方沟通京东侧资源置换方案', 'pending'),
(1, 8, 'P0', '增长机会', '美的全屋智能战略：厨电资源倾斜', '美的集团发布全屋智能新战略，厨小事业部作为核心品类将获得更多研发和营销资源。', '建议推进京东侧联合营销与新品首发方案', 'pending'),
(2, 3, 'P0', '风险预警', '九阳K系列抖音热销 · JD谈判停滞', 'JD库存深度不足，抖音侧热卖而JD缺货/缺价并存。', '建议48h内推进K9 Pro包销价与618专区库存锁定', 'pending'),
(5, 4, 'P1', '风险预警', '摩飞运营总监离职待确认', '猎头渠道显示摩飞正在招聘电商运营总监。建议主动联系确认并评估对已推进合作的影响。', '补全决策链信息后安排拜访', 'pending'),
(3, 5, 'P1', '增长机会', '苏泊尔Q2线上增速放缓', '线上全渠道增速放缓至5%。可能影响京东业绩压力与广告预算谈判。', '关注广告预算变化，准备应对方案', 'pending');

-- 恢复外键检查
SET FOREIGN_KEY_CHECKS = 1;
