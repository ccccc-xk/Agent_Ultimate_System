package com.logistics.smart.service;

/**
 * Schema 服务 - 读取数据库表结构
 */
public interface SchemaService {

    /**
     * 获取数据库所有表的结构信息
     */
    String getSchemaInfo();
}
