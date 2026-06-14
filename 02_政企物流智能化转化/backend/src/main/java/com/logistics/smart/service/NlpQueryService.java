package com.logistics.smart.service;

import com.logistics.smart.entity.QueryLog;

import java.util.List;
import java.util.Map;

/**
 * 大白话查询服务
 */
public interface NlpQueryService {

    /**
     * 自然语言查询入口
     */
    Map<String, Object> executeNaturalQuery(String question, Long userId);

    /**
     * 获取查询历史
     */
    List<QueryLog> getHistory(int limit);

    /**
     * 删除查询历史
     */
    void deleteHistory(Long id);

    /**
     * 更新查询历史的自然语言问题
     */
    void updateHistoryQuestion(Long id, String question);
}
