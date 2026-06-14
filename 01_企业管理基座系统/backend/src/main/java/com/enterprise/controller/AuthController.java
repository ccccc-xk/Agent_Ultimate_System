package com.enterprise.controller;

import com.enterprise.common.R;
import com.enterprise.dto.LoginDTO;
import com.enterprise.service.UserService;
import com.enterprise.vo.UserInfoVO;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @Autowired
    private UserService userService;

    @PostMapping("/login")
    public R<UserInfoVO> login(@Valid @RequestBody LoginDTO dto) {
        UserInfoVO vo = userService.login(dto);
        return R.ok(vo);
    }

    @GetMapping("/info")
    public R<UserInfoVO> info(HttpServletRequest request) {
        Long userId = (Long) request.getAttribute("userId");
        return R.ok(userService.getUserInfo(userId));
    }
}
