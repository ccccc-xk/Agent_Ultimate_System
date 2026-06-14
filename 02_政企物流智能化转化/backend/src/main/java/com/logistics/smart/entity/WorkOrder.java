package com.logistics.smart.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName(value = "t_work_order", autoResultMap = true)
public class WorkOrder {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String location;

    private String clientName;

    private String issue;

    /** JSON数组 - 已采取措施，MyBatis-Plus 自动处理 */
    @TableField(typeHandler = com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler.class, updateStrategy = FieldStrategy.ALWAYS)
    private java.util.List<String> actionsTaken;

    private String assignedTo;

    /** URGENT / NORMAL */
    private String priority;

    /** PENDING / PROCESSING / DONE */
    private String status;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
