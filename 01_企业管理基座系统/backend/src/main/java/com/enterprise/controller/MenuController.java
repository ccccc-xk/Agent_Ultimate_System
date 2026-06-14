package com.enterprise.controller;

import com.enterprise.common.R;
import com.enterprise.service.MenuService;
import com.enterprise.vo.MenuVO;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/menu")
public class MenuController {

    @Autowired
    private MenuService menuService;

    @GetMapping("/list")
    public R<List<MenuVO>> list(HttpServletRequest request) {
        Long userId = (Long) request.getAttribute("userId");
        return R.ok(menuService.getMenusByUserId(userId));
    }

    @GetMapping("/all")
    public R<List<MenuVO>> allTree() {
        return R.ok(menuService.listAllTree());
    }
}
