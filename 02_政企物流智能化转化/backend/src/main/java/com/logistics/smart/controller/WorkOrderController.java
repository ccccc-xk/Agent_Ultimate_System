package com.logistics.smart.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.logistics.smart.dto.ApiResult;
import com.logistics.smart.dto.WorkOrderStatusRequest;
import com.logistics.smart.entity.WorkOrder;
import com.logistics.smart.service.WorkOrderService;
import com.logistics.smart.websocket.NotificationWebSocketHandler;
import jakarta.validation.Valid;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import java.util.HashMap;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/work-order")
public class WorkOrderController {

    private final WorkOrderService workOrderService;
    private final NotificationWebSocketHandler wsHandler;

    public WorkOrderController(WorkOrderService workOrderService,
                                NotificationWebSocketHandler wsHandler) {
        this.workOrderService = workOrderService;
        this.wsHandler = wsHandler;
    }

    @GetMapping("/stats")
    public ApiResult<Map<String, Object>> stats() {
        Map<String, Object> stats = new HashMap<>();
        stats.put("total", workOrderService.countByStatus(null));
        stats.put("pending", workOrderService.countByStatus("PENDING"));
        stats.put("processing", workOrderService.countByStatus("PROCESSING"));
        stats.put("completed", workOrderService.countByStatus("COMPLETED"));
        stats.put("urgent", workOrderService.countByPriority("URGENT"));
        return ApiResult.success(stats);
    }

    @GetMapping("/list")
    public ApiResult<IPage<WorkOrder>> list(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String priority) {
        Page<WorkOrder> pageParam = new Page<>(page, size);
        IPage<WorkOrder> result = workOrderService.listByPage(pageParam, status, priority);
        return ApiResult.success(result);
    }

    @GetMapping("/{id}")
    public ApiResult<WorkOrder> detail(@PathVariable Long id) {
        return ApiResult.success(workOrderService.getById(id));
    }

    @PutMapping("/status")
    public ApiResult<WorkOrder> updateStatus(@Valid @RequestBody WorkOrderStatusRequest request) {
        WorkOrder order = workOrderService.updateStatus(request.getId(), request.getStatus());
        wsHandler.notifyStatusChange(order);
        return ApiResult.success("OK", order);
    }

    @PutMapping
    public ApiResult<WorkOrder> update(@RequestBody com.logistics.smart.dto.WorkOrderUpdateRequest request) {
        WorkOrder order = workOrderService.updateWorkOrder(request.getId(), request.getLocation(), request.getClientName(), request.getIssue(), request.getActionsTaken(), request.getAssignedTo(), request.getPriority(), request.getStatus());
        return ApiResult.success("OK", order);
    }

    @DeleteMapping("/{id}")
    public ApiResult<Void> delete(@PathVariable Long id) {
        workOrderService.deleteById(id);
        return ApiResult.success("OK", null);
    }
}