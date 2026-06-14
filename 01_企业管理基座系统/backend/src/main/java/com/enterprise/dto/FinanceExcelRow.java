package com.enterprise.dto;

import com.alibaba.excel.annotation.ExcelProperty;
import lombok.Data;

@Data
public class FinanceExcelRow {

    @ExcelProperty("\u6708\u4efd")
    private String month;

    @ExcelProperty("\u8425\u4e1a\u989d(\u4e07\u5143)")
    private String revenue;

    @ExcelProperty("\u5229\u6da6(\u4e07\u5143)")
    private String profit;

    @ExcelProperty("\u4eba\u529b\u6210\u672c(\u4e07\u5143)")
    private String laborCost;
}