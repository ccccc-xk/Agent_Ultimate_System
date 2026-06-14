package com.enterprise;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.enterprise.mapper")
public class EnterpriseBaseApplication {
    public static void main(String[] args) {
        SpringApplication.run(EnterpriseBaseApplication.class, args);
    }
}
