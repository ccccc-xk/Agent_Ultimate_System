#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据清洗脚本：去重、格式校验、过滤无效/过短条目
输出清洗报告
"""

import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_PATH = os.path.join(BASE_DIR, "data", "raw", "train_all.json")
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "cleaned", "train_clean.json")


def edit_distance(s1, s2):
    """计算两个字符串的编辑距离"""
    m, n = len(s1), len(s2)
    if m == 0 or n == 0:
        return max(m, n)

    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i-1] == s2[j-1] else 1
            dp[i][j] = min(
                dp[i-1][j] + 1,
                dp[i][j-1] + 1,
                dp[i-1][j-1] + cost
            )
    return dp[m][n]


def validate_sample(sample):
    """校验单条数据格式，返回 (is_valid, reason)"""
    # 字段存在性
    for field in ["instruction", "input", "output"]:
        if field not in sample or not isinstance(sample[field], str) or not sample[field].strip():
            return False, f"字段 {field} 缺失或为空"

    instruction = sample["instruction"].strip()
    input_text = sample["input"].strip()
    output_text = sample["output"].strip()
    category = sample.get("category", "")

    # 长度检查
    if len(input_text) < 10:
        return False, f"input 过短 ({len(input_text)} 字符 < 10)"
    if len(output_text) < 5:
        return False, f"output 过短 ({len(output_text)} 字符 < 5)"

    # 场景校验
    if category == "complaint":
        if "【分类】" not in output_text:
            return False, "complaint output 缺少【分类】标签"
        if "【核心诉求】" not in output_text:
            return False, "complaint output 缺少【核心诉求】标签"

    elif category == "workorder":
        try:
            data = json.loads(output_text)
            if not isinstance(data, dict):
                return False, "workorder output 不是 JSON 对象"
            for key in ["location", "client_name", "issue", "actions_taken", "assigned_to", "priority"]:
                if key not in data:
                    return False, f"workorder JSON 缺少字段: {key}"
            if not isinstance(data["actions_taken"], list):
                return False, "workorder actions_taken 不是数组"
        except json.JSONDecodeError as e:
            return False, f"workorder output JSON 解析失败: {e}"

    elif category == "nl2sql":
        sql = output_text.strip()
        if not sql.upper().startswith("SELECT"):
            return False, f"nl2sql output 不以 SELECT 开头: {sql[:30]}"
        # 检查是否含有代码块标记
        if "```" in sql:
            return False, "nl2sql output 含有 ``` 代码块标记"

    return True, ""


def is_fuzzy_duplicate(s1, s2, max_dist=5, min_ratio=0.8):
    """模糊去重检查"""
    if len(s1) == 0 or len(s2) == 0:
        return False
    dist = edit_distance(s1, s2)
    ratio = 1 - dist / max(len(s1), len(s2))
    return dist < max_dist and ratio > min_ratio


def clean(samples):
    """执行全部清洗步骤"""
    report = {
        "original_count": len(samples),
        "after_exact_dedup": 0,
        "after_fuzzy_dedup": 0,
        "after_validation": 0,
        "exact_duplicates_removed": 0,
        "fuzzy_duplicates_removed": 0,
        "validation_failures": 0,
        "validation_failure_reasons": {},
        "category_distribution": {},
    }

    # 步骤1: 精确去重
    exact_seen = set()
    after_exact = []
    for sample in samples:
        key = (sample.get("instruction", ""), sample.get("input", ""))
        if key not in exact_seen:
            exact_seen.add(key)
            after_exact.append(sample)
        else:
            report["exact_duplicates_removed"] += 1

    report["after_exact_dedup"] = len(after_exact)
    print(f"精确去重: {len(samples)} -> {len(after_exact)} (移除 {report['exact_duplicates_removed']})")

    # 步骤2: 模糊去重
    after_fuzzy = []
    fuzzy_seen_inputs = []
    for sample in after_exact:
        input_text = sample.get("input", "")
        is_dup = False
        for seen_input in fuzzy_seen_inputs:
            if is_fuzzy_duplicate(input_text, seen_input):
                is_dup = True
                report["fuzzy_duplicates_removed"] += 1
                break
        if not is_dup:
            after_fuzzy.append(sample)
            fuzzy_seen_inputs.append(input_text)

    report["after_fuzzy_dedup"] = len(after_fuzzy)
    print(f"模糊去重: {len(after_exact)} -> {len(after_fuzzy)} (移除 {report['fuzzy_duplicates_removed']})")

    # 步骤3: 格式校验
    after_validation = []
    for sample in after_fuzzy:
        is_valid, reason = validate_sample(sample)
        if is_valid:
            after_validation.append(sample)
        else:
            report["validation_failures"] += 1
            report["validation_failure_reasons"][reason] = report["validation_failure_reasons"].get(reason, 0) + 1

    report["after_validation"] = len(after_validation)
    print(f"格式校验: {len(after_fuzzy)} -> {len(after_validation)} (移除 {report['validation_failures']})")

    # 统计场景分布
    for sample in after_validation:
        cat = sample.get("category", "unknown")
        report["category_distribution"][cat] = report["category_distribution"].get(cat, 0) + 1

    return after_validation, report


def main():
    if not os.path.exists(INPUT_PATH):
        print(f"[ERROR] 输入文件不存在: {INPUT_PATH}")
        print("  请先运行 merge_datasets.py")
        return

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        samples = json.load(f)

    print(f"读取数据: {len(samples)} 条\n")

    cleaned, report = clean(samples)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    print(f"\n=== 清洗报告 ===")
    print(f"  原始数据: {report['original_count']} 条")
    print(f"  精确去重: -{report['exact_duplicates_removed']} 条")
    print(f"  模糊去重: -{report['fuzzy_duplicates_removed']} 条")
    print(f"  格式校验: -{report['validation_failures']} 条")
    print(f"  最终数据: {report['after_validation']} 条")
    print(f"  场景分布: {report['category_distribution']}")

    if report["validation_failure_reasons"]:
        print(f"\n  校验失败原因:")
        for reason, count in report["validation_failure_reasons"].items():
            print(f"    [{count}次] {reason}")

    print(f"\n  输出路径: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
