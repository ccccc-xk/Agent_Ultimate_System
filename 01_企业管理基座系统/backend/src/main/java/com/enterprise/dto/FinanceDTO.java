package com.enterprise.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;
import java.math.BigDecimal;

@Data
public class FinanceDTO {
    private Long id;
    @NotBlank(message = "月份不能为空")
    private String month;
    private BigDecimal revenue;
    private BigDecimal profit;
    private BigDecimal laborCost;
}
