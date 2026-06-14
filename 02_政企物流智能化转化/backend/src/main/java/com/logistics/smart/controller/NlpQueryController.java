package com.logistics.smart.controller;

import com.logistics.smart.dto.ApiResult;
import com.logistics.smart.dto.NlpQueryRequest;
import com.logistics.smart.entity.QueryLog;
import com.logistics.smart.service.NlpQueryService;
import jakarta.validation.Valid;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 大白话智能查库接口
 */
@Slf4j
@RestController
@RequestMapping("/api/nlp")
public class NlpQueryController {

    private final NlpQueryService nlpQueryService;

    public NlpQueryController(NlpQueryService nlpQueryService) {
        this.nlpQueryService = nlpQueryService;
    }

    /**
     * POST /api/nlp/query
     * 自然语言查询，大模型生成 SQL 并执行
     */
    @PostMapping("/query")
    public ApiResult<Map<String, Object>> query(@Valid @RequestBody NlpQueryRequest request) {
        log.info("收到查询请求: {}", request.getQuestion());
        Map<String, Object> result = nlpQueryService.executeNaturalQuery(request.getQuestion(), null);
        return ApiResult.success("查询成功", result);
    }

    /**
     * GET /api/nlp/query/history
     * 获取查询历史记录
     */
    @GetMapping("/query/history")
    public ApiResult<List<QueryLog>> history(
            @RequestParam(defaultValue = "20") int limit) {
        List<QueryLog> history = nlpQueryService.getHistory(limit);
        return ApiResult.success(history);
    }

    /**
     * DELETE /api/nlp/query/history/{id}
     * 删除查询历史记录
     */
    @DeleteMapping("/query/history/{id}")
    public ApiResult<Void> deleteHistory(@PathVariable Long id) {
        log.info("删除查询历史: id={}", id);
        nlpQueryService.deleteHistory(id);
        return ApiResult.success("删除成功", null);
    }

    /**
     * PUT /api/nlp/query/history/{id}
     * 编辑查询历史（更新问题描述）
     */
    @PutMapping("/query/history/{id}")
    public ApiResult<Void> updateHistory(@PathVariable Long id,
                                         @RequestBody Map<String, String> body) {
        String question = body.get("question");
        log.info("编辑查询历史: id={}, question={}", id, question);
        nlpQueryService.updateHistoryQuestion(id, question);
        return ApiResult.success("更新成功", null);
    }
}
