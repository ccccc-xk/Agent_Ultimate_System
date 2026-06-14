package com.logistics.smart.service;

import com.logistics.smart.dto.NlpExtractionResult;

/**
 * NLP 服务 - 调用大模型进行文本理解
 */
public interface NlpService {

    /**
     * 从口语化文本中提取结构化信息（NER）
     */
    NlpExtractionResult extractWorkOrderInfo(String text);

    /**
     * 将自然语言问题转换为 SQL
     */
    String generateSql(String question, String schemaInfo);
}
