package com.enterprise.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

@Data
@TableName("t_role_menu")
public class RoleMenu {
    private Long roleId;
    private Long menuId;
}
