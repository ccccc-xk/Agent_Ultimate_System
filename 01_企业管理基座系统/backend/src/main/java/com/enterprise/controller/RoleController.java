package com.enterprise.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.enterprise.common.R;
import com.enterprise.dto.RoleDTO;
import com.enterprise.entity.Role;
import com.enterprise.service.RoleService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/role")
public class RoleController {

    @Autowired
    private RoleService roleService;

    @GetMapping("/page")
    public R<IPage<Role>> page(
            @RequestParam(defaultValue = "1") int pageNum,
            @RequestParam(defaultValue = "10") int pageSize,
            @RequestParam(required = false) String keyword) {
        return R.ok(roleService.pageQuery(pageNum, pageSize, keyword));
    }

    @GetMapping("/list")
    public R<List<Role>> list() {
        return R.ok(roleService.listAll());
    }

    @PostMapping
    public R<Void> add(@Valid @RequestBody RoleDTO dto) {
        roleService.addRole(dto);
        return R.ok();
    }

    @PutMapping
    public R<Void> update(@Valid @RequestBody RoleDTO dto) {
        roleService.updateRole(dto);
        return R.ok();
    }

    @DeleteMapping("/{id}")
    public R<Void> delete(@PathVariable Long id) {
        roleService.deleteRole(id);
        return R.ok();
    }
}
