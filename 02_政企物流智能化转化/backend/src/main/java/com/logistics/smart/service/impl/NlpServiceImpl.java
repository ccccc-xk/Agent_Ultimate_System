package com.logistics.smart.service.impl;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import dev.langchain4j.model.chat.ChatLanguageModel;
import com.logistics.smart.dto.NlpExtractionResult;
import com.logistics.smart.service.NlpService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j
@Service
public class NlpServiceImpl implements NlpService {

    private final ChatLanguageModel chatModel;
    private final ObjectMapper objectMapper;

    public NlpServiceImpl(ChatLanguageModel chatModel, ObjectMapper objectMapper) {
        this.chatModel = chatModel;
        this.objectMapper = objectMapper;
    }

    @Override
    public NlpExtractionResult extractWorkOrderInfo(String text) {
        String prompt = "分析以下文本，提取事件、地点、人物、紧急度，返回纯JSON格式，严禁包含```json标记，若无提及则填null。\n" +
                "输出格式：{\"location\":\"...\", \"clientName\":\"...\", \"issue\":\"...\", \"actionsTaken\":[\"...\"], \"assignedTo\":\"...\", \"priority\":\"URGENT或NORMAL\"}\n\n" +
                "注意：\n" +
                "- location: 具体地点\n" +
                "- clientName: 客户/报事人姓名\n" +
                "- issue: 核心故障/问题描述\n" +
                "- actionsTaken: 已采取的措施列表\n" +
                "- assignedTo: 指派/通知的人员\n" +
                "- priority: 如果文本中有紧急、马上、赶紧、急、热、冷、漏水等关键词，设为URGENT，否则NORMAL\n\n" +
                "文本内容：\n" + text;

        log.info("调用大模型进行 NER 提取...");
        String response = chatModel.generate(prompt);
        log.info("大模型 NER 返回: {}", response);

        String json = response.trim();
        if (json.startsWith("```")) {
            json = json.replaceAll("```json\\s*", "").replaceAll("```\\s*", "").trim();
        }

        try {
            return objectMapper.readValue(json, NlpExtractionResult.class);
        } catch (JsonProcessingException e) {
            log.error("NER 结果解析失败: {}", json, e);
            throw new RuntimeException("大模型返回格式异常，请重试");
        }
    }

    @Override
    public String generateSql(String question, String schemaInfo) {
        String prompt = "你是MySQL查询专家。根据用户的问题和下方的表结构，生成一条简单、可直接执行的SELECT语句。\n\n" +
                "## 核心规则\n" +
                "1. 只返回一条SELECT语句，不要返回多条\n" +
                "2. 禁止使用子查询、JOIN（除非用户明确要求关联多表）等复杂语法\n" +
                "3. 优先使用 SELECT * 或 SELECT 具体字段列表，确保能返回完整行数据\n" +
                "4. 可以使用表别名（如 t_work_order wo），但不要在SELECT中嵌套子查询\n" +
                "5. 返回纯SQL，不要包含任何解释、注释、markdown标记\n" +
                "6. MySQL 8.0 语法，时间用 CURDATE() 和 DATE_SUB()\n" +
                "7. 如果用户问的是统计/计数类问题，用简单的 SELECT COUNT(*) 配合 WHERE 条件\n" +
                "8. 如果用户问的是列表/查看类问题，用 SELECT * 配合 WHERE 和 ORDER BY\n" +
                "9. 如果用户问题包含多个子问题，只回答第一个最主要的问题\n\n" +
                "## 常见问题示例\n" +
                "问：帮我查一下所有紧急工单\n" +
                "答：SELECT * FROM t_work_order WHERE priority = 'URGENT' ORDER BY create_time DESC\n\n" +
                "问：最近新建了多少工单\n" +
                "答：SELECT COUNT(*) AS total FROM t_work_order WHERE create_time >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)\n\n" +
                "问：哪些工单还没处理\n" +
                "答：SELECT * FROM t_work_order WHERE status = 'PENDING' ORDER BY create_time DESC\n\n" +
                "问：查看所有PENDING状态的工单\n" +
                "答：SELECT * FROM t_work_order WHERE status = 'PENDING' ORDER BY create_time DESC\n\n" +
                "问：上个月的紧急工单\n" +
                "答：SELECT * FROM t_work_order WHERE priority = 'URGENT' AND create_time >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH) ORDER BY create_time DESC\n\n" +
                "问：各个状态分别有多少工单\n" +
                "答：SELECT status, COUNT(*) AS count FROM t_work_order GROUP BY status\n\n" +
                "问：哪个地点工单最多\n" +
                "答：SELECT location, COUNT(*) AS count FROM t_work_order GROUP BY location ORDER BY count DESC LIMIT 10\n\n" +
                "## 数据库表结构\n" + schemaInfo + "\n\n" +
                "## 用户问题\n" + question + "\n\n" +
                "直接返回一条SQL：";

        log.info("调用大模型生成 SQL...");
        String response = chatModel.generate(prompt);
        log.info("大模型 SQL 返回: {}", response);

        String sql = response.trim();
        if (sql.startsWith("```")) {
            sql = sql.replaceAll("```sql\\s*", "").replaceAll("```\\s*", "").trim();
        }
        // 去掉末尾分号
        if (sql.endsWith(";")) {
            sql = sql.substring(0, sql.length() - 1).trim();
        }
        // 如果模型返回了多条SQL，只取第一条
        if (sql.contains(";")) {
            sql = sql.substring(0, sql.indexOf(";")).trim();
            log.warn("模型返回了多条SQL，已截取第一条: {}", sql);
        }

        return sql;
    }
}
