package com.enterprise.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.enterprise.dto.LoginDTO;
import com.enterprise.dto.UserDTO;
import com.enterprise.entity.User;
import com.enterprise.vo.UserInfoVO;

public interface UserService {

    UserInfoVO login(LoginDTO dto);

    UserInfoVO getUserInfo(Long userId);

    IPage<User> pageQuery(int pageNum, int pageSize, String keyword);

    void addUser(UserDTO dto);

    void updateUser(UserDTO dto);

    void deleteUser(Long id);

    void resetPassword(Long id);
}
