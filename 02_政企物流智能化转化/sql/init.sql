-- 政企物流智能化转化 - 数据库初始化
CREATE DATABASE IF NOT EXISTS smart_logistics DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE smart_logistics;

-- 工单表
CREATE TABLE IF NOT EXISTS t_work_order (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    location VARCHAR(255) COMMENT '地点',
    client_name VARCHAR(100) COMMENT '客户姓名',
    issue TEXT COMMENT '核心故障描述',
    actions_taken JSON COMMENT '已采取措施',
    assigned_to VARCHAR(100) COMMENT '指派人员',
    priority VARCHAR(20) DEFAULT 'NORMAL' COMMENT '优先级 URGENT/NORMAL',
    status VARCHAR(20) DEFAULT 'PENDING' COMMENT '状态 PENDING/PROCESSING/DONE',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工单表';

-- 查询日志表
CREATE TABLE IF NOT EXISTS t_query_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT COMMENT '用户ID',
    natural_question TEXT COMMENT '自然语言问题',
    generated_sql TEXT COMMENT '大模型生成的SQL',
    query_result LONGTEXT COMMENT 'JSON格式查询结果',
    status VARCHAR(20) DEFAULT 'SUCCESS' COMMENT '状态 SUCCESS/FAILED',
    error_message TEXT COMMENT '错误信息',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='查询日志表';

-- 插入示例数据
INSERT INTO t_work_order (location, client_name, issue, actions_taken, assigned_to, priority, status) VALUES
('3号楼202房间', '张大爷', '电风扇损坏', '["已送冰块降温"]', '维修部小王', 'URGENT', 'DONE'),
('5号楼101室', '李阿姨', '水管漏水', '["临时关闭水阀"]', '维修部老赵', 'URGENT', 'PENDING'),
('1号楼大厅', '物业前台', '空调不制冷', '[]', '维修部小王', 'NORMAL', 'PENDING'),
('7号楼303室', '赵先生', '门锁故障', '["已安排临时换房"]', '维修部小陈', 'NORMAL', 'DONE'),
('5号楼301房间', '李师傅', '空调漏水', '["让维修部小张过去查看"]', '维修部小张', 'URGENT', 'PENDING'),
('3号楼202房间', '张大爷', '风扇坏了，天气太热了', '["拿冰块", "通知维修部的小王"]', '维修部的小王', 'URGENT', 'PROCESSING');