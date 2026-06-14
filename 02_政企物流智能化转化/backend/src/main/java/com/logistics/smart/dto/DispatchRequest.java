package com.logistics.smart.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class DispatchRequest {

    @NotBlank(message = "口语化文本不能为空")
    private String text;
}
