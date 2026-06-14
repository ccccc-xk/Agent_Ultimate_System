package com.logistics.smart.filter;

import org.springframework.stereotype.Component;

import java.util.regex.Pattern;

/**
 * 输入安全过滤器
 * - 拦截敏感词
 * - 过滤空白/无效输入
 * - 过滤 SQL 注入关键词
 */
@Component
public class InputFilter {

    /** 敏感词正则 */
    private static final Pattern SENSITIVE_PATTERN = Pattern.compile(
            "(?i)(fuck|shit|damn|操你|他妈|狗日|傻逼|白痴|脑残|垃圾人)",
            Pattern.CASE_INSENSITIVE
    );

    /** 空白/无效输入 */
    private static final Pattern BLANK_PATTERN = Pattern.compile("^\\s*$");

    /** 纯特殊字符/数字堆砌 */
    private static final Pattern JUNK_PATTERN = Pattern.compile("^[\\d\\s\\p{Punct}]{0,3}$");

    /** SQL 注入危险关键词 */
    private static final Pattern SQL_INJECTION_PATTERN = Pattern.compile(
            "(?i)(\\b(DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE|CREATE|EXEC|EXECUTE|GRANT|REVOKE)\\b|(--|;|/\\*|\\*/|xp_|sp_))"
    );

    /**
     * 检查口语化派单输入是否合法
     */
    public void validateDispatchInput(String text) {
        if (text == null || BLANK_PATTERN.matcher(text).matches()) {
            throw new IllegalArgumentException("输入内容不能为空");
        }
        if (JUNK_PATTERN.matcher(text).matches()) {
            throw new IllegalArgumentException("请输入有效的描述内容");
        }
        if (SENSITIVE_PATTERN.matcher(text).find()) {
            throw new IllegalArgumentException("输入包含敏感词，请修改后重试");
        }
        if (text.length() > 2000) {
            throw new IllegalArgumentException("输入内容过长，请限制在2000字以内");
        }
    }

    /**
     * 检查自然语言查询输入是否合法
     */
    public void validateQueryInput(String text) {
        if (text == null || BLANK_PATTERN.matcher(text).matches()) {
            throw new IllegalArgumentException("查询问题不能为空");
        }
        if (text.length() > 1000) {
            throw new IllegalArgumentException("查询问题过长，请限制在1000字以内");
        }
        if (SENSITIVE_PATTERN.matcher(text).find()) {
            throw new IllegalArgumentException("输入包含敏感词，请修改后重试");
        }
    }

    /**
     * 检查生成的 SQL 是否安全（只允许 SELECT）
     */
    public boolean isSqlSafe(String sql) {
        if (sql == null || sql.isBlank()) {
            return false;
        }
        // 去掉前后空白和注释
        String cleaned = sql.strip().replaceAll("/\\*.*?\\*/", "").replaceAll("--.*$", "").trim();

        // 必须以 SELECT 开头
        if (!cleaned.toUpperCase().startsWith("SELECT")) {
            return false;
        }

        // 检查是否包含危险关键词
        if (SQL_INJECTION_PATTERN.matcher(cleaned).find()) {
            return false;
        }

        // 不允许多语句执行
        if (cleaned.contains(";") && cleaned.indexOf(';') < cleaned.length() - 1) {
            return false;
        }

        return true;
    }
}
