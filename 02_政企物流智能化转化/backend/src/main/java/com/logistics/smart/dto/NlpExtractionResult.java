package com.logistics.smart.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 大模型 NER 提取结果
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class NlpExtractionResult {

    private String location;
    private String clientName;
    private String issue;
    private List<String> actionsTaken;
    private String assignedTo;
    /** URGENT / NORMAL */
    private String priority;
}
