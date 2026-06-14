-- PostgreSQL version of enterprise_base init

DROP TABLE IF EXISTS t_role_menu CASCADE;
DROP TABLE IF EXISTS t_user_role CASCADE;
DROP TABLE IF EXISTS t_company_finance CASCADE;
DROP TABLE IF EXISTS t_menu CASCADE;
DROP TABLE IF EXISTS t_role CASCADE;
DROP TABLE IF EXISTS t_user CASCADE;

CREATE TABLE t_user (
  id BIGSERIAL PRIMARY KEY,
  username VARCHAR(64) NOT NULL UNIQUE,
  password VARCHAR(128) NOT NULL,
  real_name VARCHAR(64) DEFAULT NULL,
  phone VARCHAR(20) DEFAULT NULL,
  status SMALLINT NOT NULL DEFAULT 1,
  create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE t_role (
  id BIGSERIAL PRIMARY KEY,
  role_name VARCHAR(64) NOT NULL,
  role_key VARCHAR(64) NOT NULL UNIQUE,
  status SMALLINT NOT NULL DEFAULT 1,
  create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE t_menu (
  id BIGSERIAL PRIMARY KEY,
  menu_name VARCHAR(64) NOT NULL,
  parent_id BIGINT NOT NULL DEFAULT 0,
  path VARCHAR(128) DEFAULT NULL,
  component VARCHAR(128) DEFAULT NULL,
  icon VARCHAR(64) DEFAULT NULL,
  menu_type CHAR(1) NOT NULL,
  perms VARCHAR(128) DEFAULT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  status SMALLINT NOT NULL DEFAULT 1,
  create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE t_user_role (
  user_id BIGINT NOT NULL,
  role_id BIGINT NOT NULL,
  PRIMARY KEY (user_id, role_id)
);

CREATE TABLE t_role_menu (
  role_id BIGINT NOT NULL,
  menu_id BIGINT NOT NULL,
  PRIMARY KEY (role_id, menu_id)
);

CREATE TABLE t_company_finance (
  id BIGSERIAL PRIMARY KEY,
  month VARCHAR(7) NOT NULL UNIQUE,
  revenue NUMERIC(12,2) NOT NULL DEFAULT 0.00,
  profit NUMERIC(12,2) NOT NULL DEFAULT 0.00,
  labor_cost NUMERIC(12,2) NOT NULL DEFAULT 0.00,
  create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Init roles
INSERT INTO t_role (id, role_name, role_key, status) VALUES
(1, 'Super Admin', 'admin', 1),
(2, 'Staff', 'staff', 1);

-- Init users (password: 123456)
INSERT INTO t_user (id, username, password, real_name, phone, status) VALUES
(1, 'admin', '$2a$10$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36Luk4dIE1C7FKJN7tGqWre', 'Admin', '13800000001', 1),
(2, 'staff01', '$2a$10$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36Luk4dIE1C7FKJN7tGqWre', 'Staff01', '13800000002', 1);

-- User-Role mapping
INSERT INTO t_user_role (user_id, role_id) VALUES (1, 1), (2, 2);

-- Menus
INSERT INTO t_menu (id, menu_name, parent_id, path, component, icon, menu_type, perms, sort_order, status) VALUES
(1, 'Dashboard', 0, '/dashboard', 'dashboard/index', 'DataBoard', 'M', NULL, 1, 1),
(2, 'Finance', 0, '/finance', 'finance/index', 'Money', 'M', NULL, 2, 1),
(3, 'System', 0, '/system', NULL, 'Setting', 'M', NULL, 3, 1),
(4, 'Finance Report', 2, '/finance/report', 'finance/report/index', 'Document', 'C', 'finance:report:list', 1, 1),
(5, 'User Management', 3, '/system/user', 'system/user/index', 'User', 'C', 'system:user:list', 1, 1),
(6, 'Role Management', 3, '/system/role', 'system/role/index', 'UserFilled', 'C', 'system:role:list', 2, 1),
(7, 'User Add', 5, NULL, NULL, NULL, 'F', 'system:user:add', 1, 1),
(8, 'User Edit', 5, NULL, NULL, NULL, 'F', 'system:user:edit', 2, 1),
(9, 'User Delete', 5, NULL, NULL, NULL, 'F', 'system:user:delete', 3, 1),
(10, 'Role Add', 6, NULL, NULL, NULL, 'F', 'system:role:add', 1, 1),
(11, 'Role Edit', 6, NULL, NULL, NULL, 'F', 'system:role:edit', 2, 1);

-- Admin gets all permissions
INSERT INTO t_role_menu (role_id, menu_id) VALUES
(1,1),(1,2),(1,3),(1,4),(1,5),(1,6),(1,7),(1,8),(1,9),(1,10),(1,11);

-- Staff gets dashboard + finance
INSERT INTO t_role_menu (role_id, menu_id) VALUES (2,1),(2,2),(2,4);

-- Finance sample data
INSERT INTO t_company_finance (month, revenue, profit, labor_cost) VALUES
('2024-07', 520.00, 85.00, 190.00),
('2024-08', 498.00, 78.00, 192.00),
('2024-09', 610.00, 105.00, 195.00),
('2024-10', 580.00, 96.00, 193.00),
('2024-11', 650.00, 120.00, 198.00),
('2024-12', 720.00, 145.00, 205.00),
('2025-01', 530.00, 80.00, 210.00),
('2025-02', 480.00, 68.00, 208.00),
('2025-03', 640.00, 112.00, 212.00),
('2025-04', 690.00, 130.00, 215.00),
('2025-05', 750.00, 155.00, 218.00),
('2025-06', 810.00, 172.00, 220.00);

SELECT setval('t_user_id_seq', 10);
SELECT setval('t_role_id_seq', 10);
SELECT setval('t_menu_id_seq', 20);
SELECT setval('t_company_finance_id_seq', 100);
