package com.enterprise.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.enterprise.dto.FinanceDTO;
import com.enterprise.dto.FinanceExcelRow;
import com.enterprise.entity.CompanyFinance;
import com.enterprise.entity.User;
import com.enterprise.mapper.CompanyFinanceMapper;
import com.enterprise.mapper.UserMapper;
import com.enterprise.service.FinanceService;
import com.enterprise.vo.DashboardVO;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;

@Service
public class FinanceServiceImpl implements FinanceService {

    @Autowired private CompanyFinanceMapper financeMapper;
    @Autowired private UserMapper userMapper;

    @Value("${ai.api-key}")
    private String apiKey;

    @Value("${ai.api-url}")
    private String apiUrl;

    @Value("${ai.model}")
    private String model;

    @Override
    public IPage<CompanyFinance> pageQuery(int pageNum, int pageSize, String month) {
        LambdaQueryWrapper<CompanyFinance> wrapper = new LambdaQueryWrapper<>();
        if (StringUtils.hasText(month)) {
            wrapper.like(CompanyFinance::getMonth, month);
        }
        wrapper.orderByDesc(CompanyFinance::getMonth);
        return financeMapper.selectPage(new Page<>(pageNum, pageSize), wrapper);
    }

    @Override
    public void saveFinance(FinanceDTO dto) {
        Long count = financeMapper.selectCount(
                new LambdaQueryWrapper<CompanyFinance>().eq(CompanyFinance::getMonth, dto.getMonth()));
        if (count > 0) throw new RuntimeException("\u8be5\u6708\u4efd\u6570\u636e\u5df2\u5b58\u5728");

        CompanyFinance entity = new CompanyFinance();
        entity.setMonth(dto.getMonth());
        entity.setRevenue(dto.getRevenue());
        entity.setProfit(dto.getProfit());
        entity.setLaborCost(dto.getLaborCost());
        financeMapper.insert(entity);
    }

    @Override
    public void updateFinance(FinanceDTO dto) {
        CompanyFinance entity = financeMapper.selectById(dto.getId());
        if (entity == null) throw new RuntimeException("\u6570\u636e\u4e0d\u5b58\u5728");
        entity.setMonth(dto.getMonth());
        entity.setRevenue(dto.getRevenue());
        entity.setProfit(dto.getProfit());
        entity.setLaborCost(dto.getLaborCost());
        financeMapper.updateById(entity);
    }

    @Override
    public void deleteFinance(Long id) {
        financeMapper.deleteById(id);
    }

    @Override
    public CompanyFinance getByMonth(String month) {
        return financeMapper.selectOne(
                new LambdaQueryWrapper<CompanyFinance>().eq(CompanyFinance::getMonth, month));
    }

    @Override
    public DashboardVO getDashboardSummary() {
        List<CompanyFinance> all = financeMapper.selectList(
                new LambdaQueryWrapper<CompanyFinance>().orderByDesc(CompanyFinance::getMonth));
        DashboardVO vo = new DashboardVO();

        if (!all.isEmpty()) {
            CompanyFinance latest = all.get(0);
            vo.setCurrentMonthRevenue(latest.getRevenue());
            vo.setCurrentMonthProfit(latest.getProfit());
            vo.setCurrentMonthLaborCost(latest.getLaborCost());

            if (all.size() >= 2) {
                CompanyFinance prev = all.get(1);
                if (prev.getRevenue().compareTo(BigDecimal.ZERO) > 0) {
                    vo.setRevenueGrowthRate(latest.getRevenue().subtract(prev.getRevenue())
                            .divide(prev.getRevenue(), 4, RoundingMode.HALF_UP)
                            .multiply(new BigDecimal("100")).setScale(2, RoundingMode.HALF_UP));
                }
                if (prev.getProfit().compareTo(BigDecimal.ZERO) > 0) {
                    vo.setProfitGrowthRate(latest.getProfit().subtract(prev.getProfit())
                            .divide(prev.getProfit(), 4, RoundingMode.HALF_UP)
                            .multiply(new BigDecimal("100")).setScale(2, RoundingMode.HALF_UP));
                }
            }
        }

        vo.setTotalEmployees(Math.toIntExact(userMapper.selectCount(null)));

        List<DashboardVO.FinanceTrendVO> trends = new ArrayList<>();
        int limit = Math.min(all.size(), 12);
        for (int i = limit - 1; i >= 0; i--) {
            CompanyFinance f = all.get(i);
            DashboardVO.FinanceTrendVO t = new DashboardVO.FinanceTrendVO();
            t.setMonth(f.getMonth());
            t.setRevenue(f.getRevenue());
            t.setProfit(f.getProfit());
            t.setLaborCost(f.getLaborCost());
            trends.add(t);
        }
        vo.setTrends(trends);

        return vo;
    }

    @Override
    public String generateAiSummary(String month) {
        CompanyFinance finance = getByMonth(month);
        if (finance == null) throw new RuntimeException("\u672a\u627e\u5230 " + month + " \u7684\u8d22\u52a1\u6570\u636e");

        // If no real API key configured, use local rule engine directly
        if (apiKey == null || apiKey.isBlank() || apiKey.contains("your-api-key")) {
            return generateLocalSummary(finance);
        }

        String prompt = String.format(
                "\u8bf7\u6839\u636e\u4ee5\u4e0b\u4f01\u4e1a\u8d22\u52a1\u6570\u636e\uff0c\u751f\u6210\u4e00\u6bb5150\u5b57\u4ee5\u5185\u7684\u8fd0\u8425\u98ce\u9669\u63d0\u793a\uff0c\u8bed\u6c14\u8981\u5c16\u9510\u3001\u5ba2\u89c2\u3002" +
                "\u8425\u4e1a\u989d\uff1a%s\u4e07\u5143\uff0c\u5229\u6da6\uff1a%s\u4e07\u5143\uff0c\u4eba\u529b\u6210\u672c\uff1a%s\u4e07\u5143\u3002",
                finance.getRevenue(), finance.getProfit(), finance.getLaborCost());

        try {
            return callAiApi(prompt);
        } catch (Exception e) {
            return generateLocalSummary(finance);
        }
    }

    private String callAiApi(String prompt) throws Exception {
        ObjectMapper mapper = new ObjectMapper();

        String body = mapper.writeValueAsString(java.util.Map.of(
                "model", model,
                "messages", java.util.List.of(
                        java.util.Map.of("role", "system", "content", "\u4f60\u662f\u4e00\u4f4d\u8d44\u6df1\u4f01\u4e1a\u8d22\u52a1\u5206\u6790\u5e08\u3002"),
                        java.util.Map.of("role", "user", "content", prompt)
                ),
                "temperature", 0.7,
                "max_tokens", 300
        ));

        HttpClient client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(10))
                .build();

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(apiUrl))
                .header("Content-Type", "application/json")
                .header("Authorization", "Bearer " + apiKey)
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .timeout(Duration.ofSeconds(30))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() != 200) {
            throw new RuntimeException("AI API \u8c03\u7528\u5931\u8d25: HTTP " + response.statusCode());
        }

        JsonNode root = mapper.readTree(response.body());
        return root.path("choices").path(0).path("message").path("content").asText();
    }

    /** Local rule-based fallback when AI API is unavailable */
    private String generateLocalSummary(CompanyFinance f) {
        StringBuilder sb = new StringBuilder();
        BigDecimal revenue = f.getRevenue();
        BigDecimal profit = f.getProfit();
        BigDecimal laborCost = f.getLaborCost();

        // Profit rate analysis
        if (revenue.compareTo(BigDecimal.ZERO) > 0) {
            BigDecimal profitRate = profit.multiply(new BigDecimal("100"))
                    .divide(revenue, 1, RoundingMode.HALF_UP);
            if (profitRate.compareTo(new BigDecimal("20")) < 0) {
                sb.append("\u5229\u6da6\u7387\u4ec5").append(profitRate)
                  .append("%\uff0c\u4f4e\u4e8e\u5065\u5eb7\u7ebf\uff0820%\uff09\uff0c\u76c8\u5229\u80fd\u529b\u582a\u5fe7\uff0c\u5efa\u8bae\u5ba1\u89c6\u6210\u672c\u63a7\u5236\u3002");
            } else if (profitRate.compareTo(new BigDecimal("35")) > 0) {
                sb.append("\u5229\u6da6\u7387\u8fbe").append(profitRate)
                  .append("%\uff0c\u76c8\u5229\u6c34\u5e73\u4f18\u79c0\u3002\u4e0d\u8fc7\u9700\u8b66\u60d5\u9ad8\u5229\u6da6\u7387\u53ef\u80fd\u9690\u85cf\u7684\u6838\u7b97\u53e3\u5f84\u95ee\u9898\u3002");
            } else {
                sb.append("\u5229\u6da6\u7387\u4e3a").append(profitRate)
                  .append("%\uff0c\u5904\u4e8e\u884c\u4e1a\u4e2d\u7b49\u6c34\u5e73\u3002\u76c8\u5229\u80fd\u529b\u5c1a\u53ef\u4f46\u7f3a\u4e4f\u660e\u663e\u7ade\u4e89\u4f18\u52bf\u3002");
            }
        } else {
            sb.append("\u8425\u4e1a\u989d\u4e3a\u96f6\uff0c\u4f01\u4e1a\u5904\u4e8e\u65e0\u8425\u6536\u72b6\u6001\uff0c\u9700\u7acb\u5373\u5173\u6ce8\u7ecf\u8425\u72b6\u51b5\u3002");
        }

        // Labor cost analysis
        if (revenue.compareTo(BigDecimal.ZERO) > 0) {
            BigDecimal laborRatio = laborCost.multiply(new BigDecimal("100"))
                    .divide(revenue, 1, RoundingMode.HALF_UP);
            if (laborRatio.compareTo(new BigDecimal("40")) > 0) {
                sb.append("\u4eba\u529b\u6210\u672c\u5360\u6bd4\u9ad8\u8fbe").append(laborRatio)
                  .append("%\uff0c\u4e25\u91cd\u4fb5\u8680\u5229\u6da6\u7a7a\u95f4\uff0c\u5efa\u8bae\u7acb\u5373\u4f18\u5316\u4eba\u5458\u7ed3\u6784\u6216\u63d0\u5347\u4eba\u6548\u3002");
            } else if (laborRatio.compareTo(new BigDecimal("25")) > 0) {
                sb.append("\u4eba\u529b\u6210\u672c\u5360\u6bd4").append(laborRatio)
                  .append("%\uff0c\u504f\u9ad8\uff0c\u5efa\u8bae\u5173\u6ce8\u4eba\u5747\u4ea7\u51fa\u6307\u6807\u3002");
            } else {
                sb.append("\u4eba\u529b\u6210\u672c\u5360\u6bd4").append(laborRatio)
                  .append("%\uff0c\u63a7\u5236\u5f97\u5f53\u3002");
            }
        }

        // Absolute loss warning
        if (profit.compareTo(BigDecimal.ZERO) < 0) {
            sb.append("\u672c\u6708\u4e8f\u635f").append(profit.abs())
              .append("\u4e07\u5143\uff0c\u7ecf\u8425\u98ce\u9669\u5df2\u4eae\u7ea2\u706f\uff0c\u5fc5\u987b\u5728\u4e0b\u4e00\u5468\u671f\u91c7\u53d6\u6b62\u635f\u63aa\u65bd\u3002");
        }

        if (sb.length() == 0) {
            sb.append("\u8be5\u6708\u8d22\u52a1\u6570\u636e\u6570\u5b57\u5065\u5eb7\uff0c\u65e0\u660e\u663e\u98ce\u9669\u4fe1\u53f7\u3002");
        }

        return sb.toString();
    }

    @Override
    public int importFromExcel(List<FinanceExcelRow> rows) {
        int count = 0;
        for (FinanceExcelRow row : rows) {
            try {
                if (row.getMonth() == null || row.getMonth().isBlank()) continue;

                String month = row.getMonth().trim();
                BigDecimal revenue = parseBigDecimal(row.getRevenue());
                BigDecimal profit = parseBigDecimal(row.getProfit());
                BigDecimal laborCost = parseBigDecimal(row.getLaborCost());

                CompanyFinance existing = getByMonth(month);
                if (existing != null) {
                    existing.setRevenue(revenue);
                    existing.setProfit(profit);
                    existing.setLaborCost(laborCost);
                    financeMapper.updateById(existing);
                } else {
                    CompanyFinance entity = new CompanyFinance();
                    entity.setMonth(month);
                    entity.setRevenue(revenue);
                    entity.setProfit(profit);
                    entity.setLaborCost(laborCost);
                    financeMapper.insert(entity);
                }
                count++;
            } catch (Exception e) {
                // Skip bad rows silently
            }
        }
        return count;
    }

    private BigDecimal parseBigDecimal(String val) {
        if (val == null || val.isBlank()) return BigDecimal.ZERO;
        try {
            return new BigDecimal(val.trim().replace(",", ""));
        } catch (NumberFormatException e) {
            return BigDecimal.ZERO;
        }
    }
}
