package com.enterprise.controller;

import com.enterprise.common.R;
import com.enterprise.service.FinanceService;
import com.enterprise.vo.DashboardVO;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/dashboard")
public class DashboardController {

    @Autowired
    private FinanceService financeService;

    @GetMapping("/summary")
    public R<DashboardVO> summary() {
        return R.ok(financeService.getDashboardSummary());
    }
}
