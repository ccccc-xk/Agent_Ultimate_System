-- ============================================================
-- 企业管理基座系统 - 数据库初始化脚本
-- 字符集: utf8mb4  排序规则: utf8mb4_general_ci
-- ============================================================

CREATE DATABASE IF NOT EXISTS `enterprise_base` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `enterprise_base`;

-- -----------------------------------------------------------
-- 1. 用户表
-- -----------------------------------------------------------
DROP TABLE IF EXISTS `t_user`;
CREATE TABLE `t_user` (
  `id`          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键',
  `username`    VARCHAR(64)  NOT NULL COMMENT '登录账号',
  `password`    VARCHAR(128) NOT NULL COMMENT '密码(BCrypt)',
  `real_name`   VARCHAR(64)  DEFAULT NULL COMMENT '真实姓名',
  `phone`       VARCHAR(20)  DEFAULT NULL COMMENT '手机号',
  `status`      TINYINT      NOT NULL DEFAULT 1 COMMENT '状态 1=正常 0=禁用',
  `create_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- -----------------------------------------------------------
-- 2. 角色表
-- -----------------------------------------------------------
DROP TABLE IF EXISTS `t_role`;
CREATE TABLE `t_role` (
  `id`          BIGINT      NOT NULL AUTO_INCREMENT COMMENT '主键',
  `role_name`   VARCHAR(64) NOT NULL COMMENT '角色名称',
  `role_key`    VARCHAR(64) NOT NULL COMMENT '角色标识',
  `status`      TINYINT     NOT NULL DEFAULT 1 COMMENT '状态 1=正常 0=禁用',
  `create_time` DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_role_key` (`role_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色表';

-- -----------------------------------------------------------
-- 3. 菜单表
-- -----------------------------------------------------------
DROP TABLE IF EXISTS `t_menu`;
CREATE TABLE `t_menu` (
  `id`          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键',
  `menu_name`   VARCHAR(64)  NOT NULL COMMENT '菜单名称',
  `parent_id`   BIGINT       NOT NULL DEFAULT 0 COMMENT '父菜单ID(0=顶级)',
  `path`        VARCHAR(128) DEFAULT NULL COMMENT '路由地址',
  `component`   VARCHAR(128) DEFAULT NULL COMMENT '前端组件路径',
  `icon`        VARCHAR(64)  DEFAULT NULL COMMENT '菜单图标',
  `menu_type`   CHAR(1)      NOT NULL COMMENT '类型 M=目录 C=菜单 F=按钮',
  `perms`       VARCHAR(128) DEFAULT NULL COMMENT '权限标识',
  `sort_order`  INT          NOT NULL DEFAULT 0 COMMENT '排序',
  `status`      TINYINT      NOT NULL DEFAULT 1 COMMENT '状态 1=正常 0=禁用',
  `create_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='菜单表';

-- -----------------------------------------------------------
-- 4. 用户角色关联表
-- -----------------------------------------------------------
DROP TABLE IF EXISTS `t_user_role`;
CREATE TABLE `t_user_role` (
  `user_id` BIGINT NOT NULL COMMENT '用户ID',
  `role_id` BIGINT NOT NULL COMMENT '角色ID',
  PRIMARY KEY (`user_id`, `role_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户角色关联表';

-- -----------------------------------------------------------
-- 5. 角色菜单关联表
-- -----------------------------------------------------------
DROP TABLE IF EXISTS `t_role_menu`;
CREATE TABLE `t_role_menu` (
  `role_id` BIGINT NOT NULL COMMENT '角色ID',
  `menu_id` BIGINT NOT NULL COMMENT '菜单ID',
  PRIMARY KEY (`role_id`, `menu_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色菜单关联表';

-- -----------------------------------------------------------
-- 6. 财务表
-- -----------------------------------------------------------
DROP TABLE IF EXISTS `t_company_finance`;
CREATE TABLE `t_company_finance` (
  `id`          BIGINT        NOT NULL AUTO_INCREMENT COMMENT '主键',
  `month`       VARCHAR(7)    NOT NULL COMMENT '月份(yyyy-MM)',
  `revenue`     DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '营业额(万元)',
  `profit`      DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '利润(万元)',
  `labor_cost`  DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '人力成本(万元)',
  `create_time` DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_month` (`month`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='财务表';

-- ============================================================
-- 初始化数据
-- ============================================================

-- 角色
INSERT INTO `t_role` (`id`, `role_name`, `role_key`, `status`) VALUES
(1, '超级管理员', 'admin',  1),
(2, '普通员工',   'staff',  1);

-- 用户 (密码均为 123456 的 BCrypt 值)
INSERT INTO `t_user` (`id`, `username`, `password`, `real_name`, `phone`, `status`) VALUES
(1, 'admin',  '$2a$10$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36Luk4dIE1C7FKJN7tGqWre', '张管理', '13800000001', 1),
(2, 'staff01','$2a$10$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36Luk4dIE1C7FKJN7tGqWre', '李员工', '13800000002', 1);

-- 用户角色
INSERT INTO `t_user_role` (`user_id`, `role_id`) VALUES
(1, 1),
(2, 2);

-- 菜单 (5个一级 + 若干子菜单)
INSERT INTO `t_menu` (`id`, `menu_name`, `parent_id`, `path`, `component`, `icon`, `menu_type`, `perms`, `sort_order`, `status`) VALUES
-- 目录
(1, '业务数据看板', 0, '/dashboard',  'dashboard/index',  'DataBoard',    'M', NULL,                  1, 1),
(2, '财务管理',     0, '/finance',    'finance/index',    'Money',        'M', NULL,                  2, 1),
(3, '系统管理',     0, '/system',     NULL,               'Setting',      'M', NULL,                  3, 1),
-- 菜单
(4, '财务报表',     2, '/finance/report', 'finance/report/index', 'Document', 'C', 'finance:report:list', 1, 1),
(5, '用户管理',     3, '/system/user',    'system/user/index',    'User',     'C', 'system:user:list',    1, 1),
(6, '角色管理',     3, '/system/role',    'system/role/index',    'UserFilled','C', 'system:role:list',    2, 1),
-- 按钮
(7, '用户新增',     5, NULL, NULL, NULL, 'F', 'system:user:add',    1, 1),
(8, '用户编辑',     5, NULL, NULL, NULL, 'F', 'system:user:edit',   2, 1),
(9, '用户删除',     5, NULL, NULL, NULL, 'F', 'system:user:delete', 3, 1),
(10,'角色新增',     6, NULL, NULL, NULL, 'F', 'system:role:add',    1, 1),
(11,'角色编辑',     6, NULL, NULL, NULL, 'F', 'system:role:edit',   2, 1);

-- 管理员拥有全部菜单权限
INSERT INTO `t_role_menu` (`role_id`, `menu_id`) VALUES
(1,1),(1,2),(1,3),(1,4),(1,5),(1,6),(1,7),(1,8),(1,9),(1,10),(1,11);

-- 普通员工只有看板和财务报表
INSERT INTO `t_role_menu` (`role_id`, `menu_id`) VALUES
(2,1),(2,2),(2,4);

-- 财务示例数据 (2024年7月 ~ 2025年6月)
INSERT INTO `t_company_finance` (`month`, `revenue`, `profit`, `labor_cost`) VALUES
('2024-07', 520.00,  85.00, 190.00),
('2024-08', 498.00,  78.00, 192.00),
('2024-09', 610.00, 105.00, 195.00),
('2024-10', 580.00,  96.00, 193.00),
('2024-11', 650.00, 120.00, 198.00),
('2024-12', 720.00, 145.00, 205.00),
('2025-01', 530.00,  80.00, 210.00),
('2025-02', 480.00,  68.00, 208.00),
('2025-03', 640.00, 112.00, 212.00),
('2025-04', 690.00, 130.00, 215.00),
('2025-05', 750.00, 155.00, 218.00),
('2025-06', 810.00, 172.00, 220.00);
