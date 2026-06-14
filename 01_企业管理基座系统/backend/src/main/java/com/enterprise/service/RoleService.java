package com.enterprise.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.enterprise.dto.RoleDTO;
import com.enterprise.entity.Role;
import java.util.List;

public interface RoleService {

    IPage<Role> pageQuery(int pageNum, int pageSize, String keyword);

    List<Role> listAll();

    void addRole(RoleDTO dto);

    void updateRole(RoleDTO dto);

    void deleteRole(Long id);
}
