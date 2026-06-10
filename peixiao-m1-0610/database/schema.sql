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
('美的',   'midea',  'S', '周采销', 88, 72, '2-4周/次'),
('九阳',   'joyoung','A', '吴采销', 85, 85, '季度/次'),
('苏泊尔', 'supor',  'A', '陈采销', 78, 68, '季度/次'),
('小熊电器','bear',   'B', '李采销', 81, 88, '季度/次'),
('摩飞',   'morphy', 'B', '王采销', 71, 65, '季度/次');

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
(1, '2026-05-15', '10:00:00', 'regular', '产品沟通 · 空气炸锅Pro', 'completed');

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
   '- 3款新品JD首发\n- 联合投放预算600万\n- 空气炸锅Pro排期确认',
   NULL,
   'flat', '2026-06-24'),

(3, '吴采销；陈志远、赵雪',
   'K9 Pro合作沟通',
   '- K9 Pro包销价确认\n- 618库存锁定',
   NULL,
   'up', '2026-07-10'),

(6, '周采销；张磊',
   '空气炸锅Pro产品沟通',
   '- 1款空气炸锅JD首发',
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
(2, 1, '空气炸锅Pro排期确认',          'brand', 'pending',   '2026-06-15'),
(3, 2, 'K9 Pro包销价确认',             'brand', 'fulfilled', '2026-06-01'),
(3, 2, '618库存锁定',                  'brand', 'pending',   '2026-06-10'),
(6, 3, '1款空气炸锅JD首发',            'brand', 'fulfilled', '2026-05-30');

-- 待办数据
INSERT INTO todos (record_id, visit_id, priority, title, deadline, assignee, status) VALUES
(1, 2, 'P0', '跟进600万投放方案确认',       '2026-06-12', '周采销', 'pending'),
(1, 2, 'P0', '跟进空气炸锅Pro排期确认',     '2026-06-15', '周采销', 'pending'),
(1, 2, 'P1', '确认王建国岗位变动情况',       '2026-06-20', '周采销', 'pending'),
(1, 2, 'P2', '6/24下次拜访准备',           '2026-06-22', '周采销', 'pending'),
(2, 3, 'P1', '跟进K9 Pro包销价',           '2026-06-05', '吴采销', 'done'),
(2, 3, 'P2', '618库存方案确认',            '2026-06-10', '吴采销', 'pending');

-- 恢复外键检查
SET FOREIGN_KEY_CHECKS = 1;
