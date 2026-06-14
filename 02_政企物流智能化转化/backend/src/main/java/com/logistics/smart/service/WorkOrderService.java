package com.logistics.smart.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.logistics.smart.entity.WorkOrder;

/**
 * 鐎规悶鍎卞畷鐔煎嫉瀹ュ懎顫? */
public interface WorkOrderService {

    /**
     * 闁告帗绋戠紓鎾愁啅閵夈儱绀?     */
    WorkOrder create(WorkOrder workOrder);

    /**
     * 闁哄洤鐡ㄩ弻濠傤啅閵夈儱绀嬮柣妯垮煐閳?
     */
    WorkOrder updateStatus(Long id, String status);

    /**
     * 闁告帡宕氶崱娑栤偓澶愬蓟閵夘煈鍤勭€规悶鍎卞畷鐔兼晬閸喐鏆滈柟闀愯兌婵悂骞€?濞村吋锚閸樻稓鐥閻☆偊鏌呮径娑氱
     */
    IPage<WorkOrder> listByPage(Page<WorkOrder> page, String status, String priority);

    /**
     * 闁告帞濞€濞呭骸顔忛妷銉ョ
     */
    void deleteById(Long id);

    /**
     * 闁告梻濮撮·?ID 闁哄被鍎撮妤€顔忛妷銉ョ閻犲浄闄勯崕?     */
    WorkOrder getById(Long id);

    WorkOrder updateWorkOrder(Long id, String location, String clientName, String issue, java.util.List<String> actionsTaken, String assignedTo, String priority, String status);

    long countByStatus(String status);
    long countByPriority(String priority);}
