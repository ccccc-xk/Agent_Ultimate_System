package com.enterprise.service;

import com.enterprise.dto.FinanceExcelRow;
import java.util.List;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.enterprise.dto.FinanceDTO;
import com.enterprise.entity.CompanyFinance;
import com.enterprise.vo.DashboardVO;

public interface FinanceService {

    IPage<CompanyFinance> pageQuery(int pageNum, int pageSize, String month);

    void saveFinance(FinanceDTO dto);

    void updateFinance(FinanceDTO dto);

    void deleteFinance(Long id);

    CompanyFinance getByMonth(String month);

    DashboardVO getDashboardSummary();

    String generateAiSummary(String month);

    int importFromExcel(List<FinanceExcelRow> rows);
}
