#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试集划分：从清洗后数据中分层抽样，生成 holdout 验证集（20条）
输出：train_final.json + holdout_test.json
"""

import json
import os
import random

SEED = 42
TEST_SIZE = 20  # 总共抽取 20 条作为测试集
# 分层比例: complaint 7, workorder 7, nl2sql 6
TEST_DISTRIBUTION = {
    "complaint": 7,
    "workorder": 7,
    "nl2sql": 6,
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_PATH = os.path.join(BASE_DIR, "data", "cleaned", "train_clean.json")
TRAIN_OUTPUT = os.path.join(BASE_DIR, "data", "cleaned", "train_final.json")
TEST_OUTPUT = os.path.join(BASE_DIR, "data", "test", "holdout_test.json")


def main():
    random.seed(SEED)

    if not os.path.exists(INPUT_PATH):
        print(f"[ERROR] 输入文件不存在: {INPUT_PATH}")
        print("  请先运行 clean_dataset.py")
        return

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        samples = json.load(f)

    # 按 category 分组
    by_category = {}
    for sample in samples:
        cat = sample.get("category", "unknown")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(sample)

    print(f"输入数据: {len(samples)} 条")
    for cat, items in by_category.items():
        print(f"  [{cat}] {len(items)} 条")

    # 分层抽样
    test_samples = []
    train_samples = list(samples)  # 复制一份

    for category, count in TEST_DISTRIBUTION.items():
        pool = by_category.get(category, [])
        if len(pool) < count:
            print(f"[WARNING] {category} 只有 {len(pool)} 条，不足 {count} 条，全部作为测试集")
            count = len(pool)

        # 随机抽取
        indices = random.sample(range(len(pool)), count)
        selected = [pool[i] for i in indices]
        test_samples.extend(selected)

        # 从训练集中移除
        for item in selected:
            train_samples.remove(item)

    print(f"\n划分结果:")
    print(f"  训练集: {len(train_samples)} 条")
    print(f"  测试集: {len(test_samples)} 条")

    # 统计分布
    test_dist = {}
    for s in test_samples:
        cat = s.get("category", "unknown")
        test_dist[cat] = test_dist.get(cat, 0) + 1
    print(f"  测试集分布: {test_dist}")

    # 输出
    os.makedirs(os.path.dirname(TRAIN_OUTPUT), exist_ok=True)
    os.makedirs(os.path.dirname(TEST_OUTPUT), exist_ok=True)

    with open(TRAIN_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(train_samples, f, ensure_ascii=False, indent=2)

    with open(TEST_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(test_samples, f, ensure_ascii=False, indent=2)

    print(f"\n  训练集输出: {TRAIN_OUTPUT}")
    print(f"  测试集输出: {TEST_OUTPUT}")


if __name__ == "__main__":
    main()
