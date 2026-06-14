package com.logistics.smart.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.logistics.smart.entity.WorkOrder;
import com.logistics.smart.mapper.WorkOrderMapper;
import com.logistics.smart.service.WorkOrderService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Slf4j
@Service
public class WorkOrderServiceImpl implements WorkOrderService {

    private final WorkOrderMapper workOrderMapper;

    public WorkOrderServiceImpl(WorkOrderMapper workOrderMapper) {
        this.workOrderMapper = workOrderMapper;
    }

    @Override
    public WorkOrder create(WorkOrder workOrder) {
        if (workOrder.getStatus() == null) {
            workOrder.setStatus("PENDING");
        }
        if (workOrder.getPriority() == null) {
            workOrder.setPriority("NORMAL");
        }
        workOrderMapper.insert(workOrder);
        log.info("WorkOrder", workOrder.getId(), workOrder.getIssue());
        return workOrder;
    }

    @Override
    public WorkOrder updateStatus(Long id, String status) {
        WorkOrder order = workOrderMapper.selectById(id);
        if (order == null) {
            throw new IllegalArgumentException("WorkOrder" + id);
        }
        validateStatusTransition(order.getStatus(), status);
        order.setStatus(status);
        workOrderMapper.updateById(order);
        log.info("WorkOrder", id, order.getStatus(), status);
        return order;
    }

    @Override
    public IPage<WorkOrder> listByPage(Page<WorkOrder> page, String status, String priority) {
        LambdaQueryWrapper<WorkOrder> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(StringUtils.hasText(status), WorkOrder::getStatus, status)
               .eq(StringUtils.hasText(priority), WorkOrder::getPriority, priority)
               .orderByAsc(WorkOrder::getCreateTime);
        return workOrderMapper.selectPage(page, wrapper);
    }

    @Override
    public void deleteById(Long id) {
        WorkOrder order = workOrderMapper.selectById(id);
        if (order == null) {
            throw new IllegalArgumentException("WorkOrder" + id);
        }
        workOrderMapper.deleteById(id);
        log.info("WorkOrder", id);
    }

    @Override
    public WorkOrder getById(Long id) {
        WorkOrder order = workOrderMapper.selectById(id);
        if (order == null) {
            throw new IllegalArgumentException("WorkOrder" + id);
        }
        return order;
    }

    private void validateStatusTransition(String current, String target) {
        boolean valid = switch (current) {
            case "PENDING" -> "PROCESSING".equals(target);
            case "PROCESSING" -> "DONE".equals(target);
            case "DONE" -> false;
            default -> false;
        };
        if (!valid) {
            throw new IllegalArgumentException(
                    String.format("WorkOrder", current, target));
        }
    }

    @Override
    public WorkOrder updateWorkOrder(Long id, String location, String clientName, String issue,
            java.util.List<String> actionsTaken, String assignedTo, String priority, String status) {
        WorkOrder order = workOrderMapper.selectById(id);
        if (order == null) {
            throw new IllegalArgumentException("WorkOrder" + id);
        }
        if (location != null) order.setLocation(location);
        if (clientName != null) order.setClientName(clientName);
        if (issue != null) order.setIssue(issue);
        if (actionsTaken != null) order.setActionsTaken(actionsTaken);
        if (assignedTo != null) order.setAssignedTo(assignedTo);
        if (priority != null) order.setPriority(priority);
        if (status != null) order.setStatus(status);
        workOrderMapper.updateById(order);
        log.info("WorkOrder", id);
        return order;
    }

    @Override
    public long countByStatus(String status) {
        LambdaQueryWrapper<WorkOrder> wrapper = new LambdaQueryWrapper<>();
        if (status != null) {
            wrapper.eq(WorkOrder::getStatus, status);
        }
        return workOrderMapper.selectCount(wrapper);
    }

    @Override
    public long countByPriority(String priority) {
        LambdaQueryWrapper<WorkOrder> wrapper = new LambdaQueryWrapper<>();
        if (priority != null) {
            wrapper.eq(WorkOrder::getPriority, priority);
        }
        return workOrderMapper.selectCount(wrapper);
    }}
