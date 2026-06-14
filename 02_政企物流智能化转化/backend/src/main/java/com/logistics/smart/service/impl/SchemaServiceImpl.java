package com.logistics.smart.service.impl;

import com.logistics.smart.service.SchemaService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

/**
 * 从 MySQL information_schema 读取所有表结构
 */
@Slf4j
@Service
public class SchemaServiceImpl implements SchemaService {

    private final JdbcTemplate jdbcTemplate;

    public SchemaServiceImpl(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @Override
    public String getSchemaInfo() {
        StringBuilder sb = new StringBuilder();

        // 获取当前数据库名
        String dbName = jdbcTemplate.queryForObject("SELECT DATABASE()", String.class);

        // 获取所有表
        List<Map<String, Object>> tables = jdbcTemplate.queryForList(
                "SELECT TABLE_NAME, TABLE_COMMENT FROM information_schema.TABLES " +
                "WHERE TABLE_SCHEMA = ? AND TABLE_TYPE = 'BASE TABLE'", dbName);

        for (Map<String, Object> table : tables) {
            String tableName = (String) table.get("TABLE_NAME");
            String comment = (String) table.get("TABLE_COMMENT");

            sb.append("表名: ").append(tableName);
            if (comment != null && !comment.isEmpty()) {
                sb.append(" (").append(comment).append(")");
            }
            sb.append("\n");

            // 获取字段信息
            List<Map<String, Object>> columns = jdbcTemplate.queryForList(
                    "SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_COMMENT " +
                    "FROM information_schema.COLUMNS " +
                    "WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? " +
                    "ORDER BY ORDINAL_POSITION", dbName, tableName);

            sb.append("字段:\n");
            for (Map<String, Object> col : columns) {
                sb.append("  - ").append(col.get("COLUMN_NAME"))
                  .append(" ").append(col.get("COLUMN_TYPE"));
                String colComment = (String) col.get("COLUMN_COMMENT");
                if (colComment != null && !colComment.isEmpty()) {
                    sb.append(" -- ").append(colComment);
                }
                sb.append("\n");
            }
            sb.append("\n");
        }

        String schema = sb.toString();
        log.info("获取数据库 Schema:\n{}", schema);
        return schema;
    }
}
