package com.logistics.smart.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class NlpQueryRequest {

    @NotBlank(message = "查询问题不能为空")
    private String question;
}
