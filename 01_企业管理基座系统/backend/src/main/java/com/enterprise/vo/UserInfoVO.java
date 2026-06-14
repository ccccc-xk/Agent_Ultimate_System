package com.enterprise.vo;

import lombok.Data;
import java.util.List;
import java.util.Set;

@Data
public class UserInfoVO {
    private Long id;
    private String username;
    private String realName;
    private String phone;
    private Set<String> roles;
    private Set<String> permissions;
}
