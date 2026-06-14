package com.enterprise.vo;

import lombok.Data;
import java.util.List;

@Data
public class MenuVO {
    private Long id;
    private String menuName;
    private Long parentId;
    private String path;
    private String component;
    private String icon;
    private String menuType;
    private String perms;
    private Integer sortOrder;
    private List<MenuVO> children;
}
