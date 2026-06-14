-- P02 Smart Logistics - PostgreSQL init

DROP TABLE IF EXISTS t_query_log CASCADE;
DROP TABLE IF EXISTS t_work_order CASCADE;

CREATE TABLE t_work_order (
    id BIGSERIAL PRIMARY KEY,
    location VARCHAR(255),
    client_name VARCHAR(100),
    issue TEXT,
    actions_taken JSONB,
    assigned_to VARCHAR(100),
    priority VARCHAR(20) DEFAULT 'NORMAL',
    status VARCHAR(20) DEFAULT 'PENDING',
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE t_query_log (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    natural_question TEXT,
    generated_sql TEXT,
    query_result TEXT,
    status VARCHAR(20) DEFAULT 'SUCCESS',
    error_message TEXT,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO t_work_order (location, client_name, issue, actions_taken, assigned_to, priority, status) VALUES
('3号楼202房间', '张大爷', '电风扇损坏', '["已送冰块降温"]', '维修部小王', 'URGENT', 'DONE'),
('5号楼101室', '李阿姨', '水管漏水', '["临时关闭水阀"]', '维修部老赵', 'URGENT', 'PENDING'),
('1号楼大厅', '物业前台', '空调不制冷', '[]', '维修部小王', 'NORMAL', 'PENDING'),
('7号楼303室', '赵先生', '门锁故障', '["已安排临时换房"]', '维修部小陈', 'NORMAL', 'DONE'),
('5号楼301房间', '李师傅', '空调漏水', '["让维修部小张过去查看"]', '维修部小张', 'URGENT', 'PENDING'),
('3号楼202房间', '张大爷', '风扇坏了，天气太热了', '["拿冰块", "通知维修部的小王"]', '维修部的小王', 'URGENT', 'PROCESSING');

SELECT setval('t_work_order_id_seq', 100);
SELECT setval('t_query_log_id_seq', 100);
