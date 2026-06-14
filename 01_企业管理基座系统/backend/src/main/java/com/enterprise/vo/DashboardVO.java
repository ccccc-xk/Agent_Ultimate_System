package com.enterprise.vo;

import lombok.Data;
import java.math.BigDecimal;

@Data
public class DashboardVO {
    private BigDecimal currentMonthRevenue;
    private BigDecimal currentMonthProfit;
    private BigDecimal currentMonthLaborCost;
    private Integer totalEmployees;
    private BigDecimal revenueGrowthRate;
    private BigDecimal profitGrowthRate;
    private java.util.List<FinanceTrendVO> trends;

    @Data
    public static class FinanceTrendVO {
        private String month;
        private BigDecimal revenue;
        private BigDecimal profit;
        private BigDecimal laborCost;
    }
}
