package com.enterprise.service;

import com.enterprise.entity.Menu;
import com.enterprise.vo.MenuVO;
import java.util.List;

public interface MenuService {

    List<MenuVO> getMenusByUserId(Long userId);

    List<MenuVO> listAllTree();

    List<Menu> listAll();

    void saveMenu(Menu menu);

    void updateMenu(Menu menu);

    void deleteMenu(Long id);
}
