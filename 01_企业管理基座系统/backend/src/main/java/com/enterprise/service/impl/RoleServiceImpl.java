package com.enterprise.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.enterprise.dto.RoleDTO;
import com.enterprise.entity.Role;
import com.enterprise.entity.RoleMenu;
import com.enterprise.mapper.RoleMapper;
import com.enterprise.mapper.RoleMenuMapper;
import com.enterprise.service.RoleService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.util.List;

@Service
public class RoleServiceImpl implements RoleService {

    @Autowired private RoleMapper roleMapper;
    @Autowired private RoleMenuMapper roleMenuMapper;

    @Override
    public IPage<Role> pageQuery(int pageNum, int pageSize, String keyword) {
        LambdaQueryWrapper<Role> wrapper = new LambdaQueryWrapper<>();
        if (StringUtils.hasText(keyword)) {
            wrapper.like(Role::getRoleName, keyword).or().like(Role::getRoleKey, keyword);
        }
        wrapper.orderByDesc(Role::getCreateTime);
        return roleMapper.selectPage(new Page<>(pageNum, pageSize), wrapper);
    }

    @Override
    public List<Role> listAll() {
        return roleMapper.selectList(new LambdaQueryWrapper<Role>().eq(Role::getStatus, 1));
    }

    @Override
    @Transactional
    public void addRole(RoleDTO dto) {
        Long count = roleMapper.selectCount(
                new LambdaQueryWrapper<Role>().eq(Role::getRoleKey, dto.getRoleKey()));
        if (count > 0) throw new RuntimeException("角色标识已存在");

        Role role = new Role();
        role.setRoleName(dto.getRoleName());
        role.setRoleKey(dto.getRoleKey());
        role.setStatus(dto.getStatus() != null ? dto.getStatus() : 1);
        roleMapper.insert(role);

        saveRoleMenus(role.getId(), dto.getMenuIds());
    }

    @Override
    @Transactional
    public void updateRole(RoleDTO dto) {
        Role role = roleMapper.selectById(dto.getId());
        if (role == null) throw new RuntimeException("角色不存在");

        role.setRoleName(dto.getRoleName());
        role.setRoleKey(dto.getRoleKey());
        if (dto.getStatus() != null) role.setStatus(dto.getStatus());
        roleMapper.updateById(role);

        // 重建菜单关联
        roleMenuMapper.delete(
                new LambdaQueryWrapper<RoleMenu>().eq(RoleMenu::getRoleId, role.getId()));
        saveRoleMenus(role.getId(), dto.getMenuIds());
    }

    @Override
    @Transactional
    public void deleteRole(Long id) {
        roleMapper.deleteById(id);
        roleMenuMapper.delete(
                new LambdaQueryWrapper<RoleMenu>().eq(RoleMenu::getRoleId, id));
    }

    private void saveRoleMenus(Long roleId, List<Long> menuIds) {
        if (menuIds != null) {
            for (Long menuId : menuIds) {
                RoleMenu rm = new RoleMenu();
                rm.setRoleId(roleId);
                rm.setMenuId(menuId);
                roleMenuMapper.insert(rm);
            }
        }
    }
}
