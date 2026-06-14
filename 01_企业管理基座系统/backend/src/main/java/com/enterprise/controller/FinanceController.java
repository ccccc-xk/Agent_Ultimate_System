package com.enterprise.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.enterprise.common.R;
import com.enterprise.dto.FinanceDTO;
import com.enterprise.entity.CompanyFinance;
import com.enterprise.dto.FinanceExcelRow;
import com.enterprise.service.FinanceService;
import com.alibaba.excel.EasyExcel;
import jakarta.servlet.http.HttpServletResponse;
import java.io.InputStream;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.List;
import com.enterprise.vo.DashboardVO;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/finance")
public class FinanceController {

    @Autowired
    private FinanceService financeService;

    @GetMapping("/page")
    public R<IPage<CompanyFinance>> page(
            @RequestParam(defaultValue = "1") int pageNum,
            @RequestParam(defaultValue = "10") int pageSize,
            @RequestParam(required = false) String month) {
        return R.ok(financeService.pageQuery(pageNum, pageSize, month));
    }

    @PostMapping
    public R<Void> add(@Valid @RequestBody FinanceDTO dto) {
        financeService.saveFinance(dto);
        return R.ok();
    }

    @PutMapping
    public R<Void> update(@Valid @RequestBody FinanceDTO dto) {
        financeService.updateFinance(dto);
        return R.ok();
    }

    @DeleteMapping("/{id}")
    public R<Void> delete(@PathVariable Long id) {
        financeService.deleteFinance(id);
        return R.ok();
    }

    @PostMapping("/ai-summary")
    public R<String> aiSummary(@RequestParam String month) {
        return R.ok(financeService.generateAiSummary(month));
    }

    @PostMapping("/import")
    public R<String> importExcel(@RequestParam("file") org.springframework.web.multipart.MultipartFile file) {
        try (InputStream is = file.getInputStream()) {
            List<FinanceExcelRow> rows = EasyExcel.read(is, FinanceExcelRow.class, null).sheet().doReadSync();
            int count = financeService.importFromExcel(rows);
            return R.ok("成功导入 " + count + " 条财务数据");
        } catch (Exception e) {
            return R.fail("导入失败: " + e.getMessage());
        }
    }

    @GetMapping("/template")
    public void downloadTemplate(HttpServletResponse response) throws Exception {
        response.setContentType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
        String fileName = URLEncoder.encode("财务数据导入模板", StandardCharsets.UTF_8).replaceAll("\\+", "%20");
        response.setHeader("Content-Disposition", "attachment;filename=" + fileName + ".xlsx");
        EasyExcel.write(response.getOutputStream(), FinanceExcelRow.class).sheet("财务数据").doWrite(List.of());
    }
}