package com.logistics.smart.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("t_query_log")
public class QueryLog {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long userId;

    private String naturalQuestion;

    private String generatedSql;

    /** JSON格式查询结果，直接存储为字符串 */
    private String queryResult;

    /** SUCCESS / FAILED */
    private String status;

    private String errorMessage;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
}
