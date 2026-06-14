#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并三个场景的数据集为统一 JSON 数组
每条记录添加 category 字段
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")

SCENE_FILES = {
    "complaint": "complaint.json",
    "workorder": "workorder.json",
    "nl2sql": "nl2sql.json",
}


def main():
    all_samples = []

    for category, filename in SCENE_FILES.items():
        filepath = os.path.join(RAW_DIR, filename)
        if not os.path.exists(filepath):
            print(f"[WARNING] 文件不存在: {filepath}，跳过")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            item["category"] = category

        all_samples.extend(data)
        print(f"  [{category}] 加载 {len(data)} 条")

    output_path = os.path.join(RAW_DIR, "train_all.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_samples, f, ensure_ascii=False, indent=2)

    print(f"\n[合并完成] 总计 {len(all_samples)} 条")
    print(f"  输出路径: {output_path}")

    # 统计各场景分布
    category_counts = {}
    for sample in all_samples:
        cat = sample.get("category", "unknown")
        category_counts[cat] = category_counts.get(cat, 0) + 1
    print(f"  场景分布: {category_counts}")


if __name__ == "__main__":
    main()
