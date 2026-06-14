package com.logistics.smart.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.logistics.smart.entity.QueryLog;
import com.logistics.smart.filter.InputFilter;
import com.logistics.smart.mapper.QueryLogMapper;
import com.logistics.smart.service.NlpQueryService;
import com.logistics.smart.service.NlpService;
import com.logistics.smart.service.SchemaService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.text.SimpleDateFormat;
import java.util.*;

@Slf4j
@Service
public class NlpQueryServiceImpl implements NlpQueryService {

    private final NlpService nlpService;
    private final SchemaService schemaService;
    private final InputFilter inputFilter;
    private final JdbcTemplate jdbcTemplate;
    private final QueryLogMapper queryLogMapper;
    private final ObjectMapper objectMapper;

    public NlpQueryServiceImpl(NlpService nlpService,
                                SchemaService schemaService,
                                InputFilter inputFilter,
                                JdbcTemplate jdbcTemplate,
                                QueryLogMapper queryLogMapper) {
        this.nlpService = nlpService;
        this.schemaService = schemaService;
        this.inputFilter = inputFilter;
        this.jdbcTemplate = jdbcTemplate;
        this.queryLogMapper = queryLogMapper;
        this.objectMapper = new ObjectMapper();
        this.objectMapper.registerModule(new JavaTimeModule());
        this.objectMapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
        this.objectMapper.setDateFormat(new SimpleDateFormat("yyyy-MM-dd HH:mm:ss"));
    }

    @Override
    public Map<String, Object> executeNaturalQuery(String question, Long userId) {
        inputFilter.validateQueryInput(question);
        String schema = schemaService.getSchemaInfo();
        String generatedSql = nlpService.generateSql(question, schema);
        log.info("Generated SQL: {}", generatedSql);

        if (!inputFilter.isSqlSafe(generatedSql)) {
            String errorMsg = "Unsafe SQL detected: " + generatedSql;
            saveQueryLog(userId, question, generatedSql, null, "FAILED", errorMsg);
            throw new IllegalArgumentException(errorMsg);
        }

        Map<String, Object> result = new LinkedHashMap<>();
        try {
            List<Map<String, Object>> rows = jdbcTemplate.queryForList(generatedSql);
            result.put("columns", rows.isEmpty() ? Collections.emptyList() : new ArrayList<>(rows.get(0).keySet()));
            result.put("rows", rows);
            result.put("rowCount", rows.size());
            result.put("sql", generatedSql);

            saveQueryLog(userId, question, generatedSql, result, "SUCCESS", null);
            log.info("Query success, returned {} rows", rows.size());

        } catch (Exception e) {
            String errorMsg = "SQL execution failed: " + e.getMessage();
            saveQueryLog(userId, question, generatedSql, null, "FAILED", errorMsg);
            throw new RuntimeException(errorMsg);
        }

        return result;
    }

    @Override
    public List<QueryLog> getHistory(int limit) {
        LambdaQueryWrapper<QueryLog> wrapper = new LambdaQueryWrapper<>();
        wrapper.orderByDesc(QueryLog::getCreateTime).last("LIMIT " + limit);
        return queryLogMapper.selectList(wrapper);
    }

    @Override
    public void deleteHistory(Long id) {
        QueryLog existing = queryLogMapper.selectById(id);
        if (existing == null) {
            throw new IllegalArgumentException("Record not found: id=" + id);
        }
        queryLogMapper.deleteById(id);
        log.info("Deleted query history id={}", id);
    }

    @Override
    public void updateHistoryQuestion(Long id, String question) {
        QueryLog existing = queryLogMapper.selectById(id);
        if (existing == null) {
            throw new IllegalArgumentException("Record not found: id=" + id);
        }
        if (question == null || question.isBlank()) {
            throw new IllegalArgumentException("Question cannot be empty");
        }
        existing.setNaturalQuestion(question);
        queryLogMapper.updateById(existing);
        log.info("Updated query history id={}, question={}", id, question);
    }

    private void saveQueryLog(Long userId, String question, String sql,
                              Object result, String status, String errorMessage) {
        try {
            QueryLog queryLog = new QueryLog();
            queryLog.setUserId(userId);
            queryLog.setNaturalQuestion(question);
            queryLog.setGeneratedSql(sql);
            queryLog.setStatus(status);
            queryLog.setErrorMessage(errorMessage);
            if (result != null) {
                try {
                    queryLog.setQueryResult(objectMapper.writeValueAsString(result));
                } catch (Exception jsonEx) {
                    queryLog.setQueryResult(result.toString());
                }
            }
            queryLogMapper.insert(queryLog);
        } catch (Exception e) {
            log.error("Failed to save query log", e);
        }
    }
}
