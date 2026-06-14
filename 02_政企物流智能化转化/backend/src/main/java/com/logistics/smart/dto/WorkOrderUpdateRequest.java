package com.logistics.smart.dto;

import lombok.Data;
import java.util.List;

@Data
public class WorkOrderUpdateRequest {

    private Long id;
    private String location;
    private String clientName;
    private String issue;
    private List<String> actionsTaken;
    private String assignedTo;
    private String priority;
    private String status;
}
