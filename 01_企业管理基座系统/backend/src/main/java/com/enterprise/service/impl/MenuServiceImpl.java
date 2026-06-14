package com.enterprise.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.enterprise.entity.Menu;
import com.enterprise.mapper.MenuMapper;
import com.enterprise.service.MenuService;
import com.enterprise.vo.MenuVO;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class MenuServiceImpl implements MenuService {

    @Autowired private MenuMapper menuMapper;

    @Override
    public List<MenuVO> getMenusByUserId(Long userId) {
        List<Menu> menus = menuMapper.selectMenusByUserId(userId);
        // 只返回 M 和 C 类型（目录和菜单），不返回按钮
        List<Menu> filtered = menus.stream()
                .filter(m -> "M".equals(m.getMenuType()) || "C".equals(m.getMenuType()))
                .collect(Collectors.toList());
        return buildTree(filtered);
    }

    @Override
    public List<MenuVO> listAllTree() {
        List<Menu> menus = menuMapper.selectList(
                new LambdaQueryWrapper<Menu>().eq(Menu::getStatus, 1).orderByAsc(Menu::getSortOrder));
        return buildTree(menus);
    }

    @Override
    public List<Menu> listAll() {
        return menuMapper.selectList(
                new LambdaQueryWrapper<Menu>().orderByAsc(Menu::getSortOrder));
    }

    @Override
    public void saveMenu(Menu menu) {
        menuMapper.insert(menu);
    }

    @Override
    public void updateMenu(Menu menu) {
        menuMapper.updateById(menu);
    }

    @Override
    public void deleteMenu(Long id) {
        menuMapper.deleteById(id);
    }

    private List<MenuVO> buildTree(List<Menu> menus) {
        List<MenuVO> voList = menus.stream().map(this::toVO).collect(Collectors.toList());
        List<MenuVO> tree = new ArrayList<>();
        for (MenuVO vo : voList) {
            if (vo.getParentId() == null || vo.getParentId() == 0) {
                tree.add(vo);
            }
        }
        for (MenuVO parent : tree) {
            parent.setChildren(findChildren(parent.getId(), voList));
        }
        return tree;
    }

    private List<MenuVO> findChildren(Long parentId, List<MenuVO> all) {
        List<MenuVO> children = all.stream()
                .filter(v -> parentId.equals(v.getParentId()))
                .collect(Collectors.toList());
        for (MenuVO child : children) {
            child.setChildren(findChildren(child.getId(), all));
        }
        return children;
    }

    private MenuVO toVO(Menu m) {
        MenuVO vo = new MenuVO();
        vo.setId(m.getId());
        vo.setMenuName(m.getMenuName());
        vo.setParentId(m.getParentId());
        vo.setPath(m.getPath());
        vo.setComponent(m.getComponent());
        vo.setIcon(m.getIcon());
        vo.setMenuType(m.getMenuType());
        vo.setPerms(m.getPerms());
        vo.setSortOrder(m.getSortOrder());
        return vo;
    }
}
