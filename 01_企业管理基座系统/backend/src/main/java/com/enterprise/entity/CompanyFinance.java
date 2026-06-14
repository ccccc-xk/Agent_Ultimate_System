package com.enterprise.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("t_company_finance")
public class CompanyFinance {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String month;
    private BigDecimal revenue;
    private BigDecimal profit;
    private BigDecimal laborCost;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
