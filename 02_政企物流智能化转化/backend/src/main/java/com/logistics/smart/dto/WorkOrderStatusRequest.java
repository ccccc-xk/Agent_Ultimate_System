package com.logistics.smart.dto;

import lombok.Data;

@Data
public class WorkOrderStatusRequest {

    private Long id;

    /** PENDING / PROCESSING / DONE */
    private String status;
}
