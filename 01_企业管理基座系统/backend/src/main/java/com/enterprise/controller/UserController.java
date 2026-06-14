package com.enterprise.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.enterprise.common.R;
import com.enterprise.dto.UserDTO;
import com.enterprise.entity.User;
import com.enterprise.service.UserService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/user")
public class UserController {

    @Autowired
    private UserService userService;

    @GetMapping("/page")
    public R<IPage<User>> page(
            @RequestParam(defaultValue = "1") int pageNum,
            @RequestParam(defaultValue = "10") int pageSize,
            @RequestParam(required = false) String keyword) {
        return R.ok(userService.pageQuery(pageNum, pageSize, keyword));
    }

    @PostMapping
    public R<Void> add(@Valid @RequestBody UserDTO dto) {
        userService.addUser(dto);
        return R.ok();
    }

    @PutMapping
    public R<Void> update(@Valid @RequestBody UserDTO dto) {
        userService.updateUser(dto);
        return R.ok();
    }

    @DeleteMapping("/{id}")
    public R<Void> delete(@PathVariable Long id) {
        userService.deleteUser(id);
        return R.ok();
    }

    @PutMapping("/reset-password/{id}")
    public R<Void> resetPassword(@PathVariable Long id) {
        userService.resetPassword(id);
        return R.ok();
    }
}
