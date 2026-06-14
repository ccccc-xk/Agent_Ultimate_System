package com.logistics.smart.controller;

import com.logistics.smart.dto.ApiResult;
import com.logistics.smart.dto.DispatchRequest;
import com.logistics.smart.dto.NlpExtractionResult;
import com.logistics.smart.entity.WorkOrder;
import com.logistics.smart.filter.InputFilter;
import com.logistics.smart.service.NlpService;
import com.logistics.smart.service.WorkOrderService;
import com.logistics.smart.websocket.NotificationWebSocketHandler;
import jakarta.validation.Valid;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.Collections;

/**
 * 口语化智能派单接口
 */
@Slf4j
@RestController
@RequestMapping("/api/nlp")
public class NlpDispatchController {

    private final NlpService nlpService;
    private final WorkOrderService workOrderService;
    private final InputFilter inputFilter;
    private final NotificationWebSocketHandler wsHandler;

    public NlpDispatchController(NlpService nlpService,
                                  WorkOrderService workOrderService,
                                  InputFilter inputFilter,
                                  NotificationWebSocketHandler wsHandler) {
        this.nlpService = nlpService;
        this.workOrderService = workOrderService;
        this.inputFilter = inputFilter;
        this.wsHandler = wsHandler;
    }

    /**
     * POST /api/nlp/dispatch
     * 接收口语化文本，大模型提取信息后自动创建工单
     */
    @PostMapping("/dispatch")
    public ApiResult<WorkOrder> dispatch(@Valid @RequestBody DispatchRequest request) {
        String text = request.getText();

        // 1. 输入安全过滤
        inputFilter.validateDispatchInput(text);
        log.info("收到派单请求: {}", text);

        // 2. 调用大模型 NER 提取
        NlpExtractionResult extraction = nlpService.extractWorkOrderInfo(text);
        log.info("NER 提取结果: {}", extraction);

        // 3. 组装工单实体
        WorkOrder order = new WorkOrder();
        order.setLocation(extraction.getLocation());
        order.setClientName(extraction.getClientName());
        order.setIssue(extraction.getIssue());
        order.setActionsTaken(extraction.getActionsTaken() != null
                ? extraction.getActionsTaken() : Collections.emptyList());
        order.setAssignedTo(extraction.getAssignedTo());
        order.setPriority(extraction.getPriority() != null
                ? extraction.getPriority() : "NORMAL");
        order.setStatus("PENDING");

        // 4. 持久化到数据库
        WorkOrder created = workOrderService.create(order);

        // 5. WebSocket 广播新工单通知
        wsHandler.notifyNewWorkOrder(created);

        log.info("工单创建成功: id={}", created.getId());
        return ApiResult.success("工单创建成功", created);
    }
}
