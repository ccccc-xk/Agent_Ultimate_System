#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场景一：投诉分类归因 — SFT 训练数据生成
instruction: "分析投诉文本，归类标签并提取诉求。"
output 格式: 【分类】：X\n【核心诉求】：Y
"""

import json
import os
import random
import hashlib

SEED = 42
TARGET_COUNT = 60
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")

# ============================================================
# 模板库
# ============================================================

EMOTION_TYPES = ["暴躁型", "委婉型", "焦急型", "讽刺型", "理性型"]

PRODUCT_TYPES = [
    "衣服", "手机", "笔记本电脑", "冰箱", "洗衣机",
    "食品", "化妆品", "鞋子", "家具", "手表"
]

ISSUE_TYPES = ["质量问题", "物流延迟", "客服态度", "虚假宣传", "售后推诿", "价格欺诈"]

DEMAND_TYPES = ["退款", "换货", "赔偿", "道歉", "补发"]

# 句式模板: {emotion}=情绪词, {product}=商品, {issue}=问题, {demand}=诉求
SENTENCE_TEMPLATES = [
    # 暴躁型
    "{emotion}我买的{product}{issue}，{demand}！别废话！",
    "气死了！{product}{issue}，必须{demand}！",
    "你们这{product}也太垃圾了吧{issue}，赶紧{demand}！",
    "什么破{product}啊{issue}，我要{demand}！",
    "买个{product}结果{issue}，我真的是无语了，{demand}！",

    # 委婉型
    "您好，我购买的{product}出现了{issue}的情况，希望能{demand}，谢谢。",
    "买了一个{product}，收到后发现{issue}，想跟您商量一下{demand}的事情。",
    "不好意思打扰了，我买的{product}{issue}，请问可以{demand}吗？",
    "{product}到了发现{issue}，感觉不太满意，能否{demand}？",
    "您好，我上次买的{product}{issue}，不知道能不能{demand}呢？",

    # 焦急型
    "急死了！{product}{issue}，明天就要用，能不能快点{demand}？",
    "这个{product}出问题了，{issue}，能不能马上处理{demand}？",
    "我等了好几天了，{product}一直{issue}，{demand}什么时候能处理？",
    "赶紧的吧，{product}{issue}，拖了这么久了，该{demand}了吧！",
    "拜托快点处理，{product}{issue}已经好几天了，{demand}！",

    # 讽刺型
    "哇，你们这{product}质量真不错啊，{issue}，真是物有所值，{demand}吧？",
    "厉害了，{product}买回来就{issue}，这服务水平真是绝了，{demand}！",
    "不错不错，{product}{issue}，你们售后服务也是够可以的，{demand}。",
    "体验了一回你们的{product}，{issue}，下次一定推荐给敌人，{demand}。",
    "你们这{product}太有创意了，{issue}，我想知道还有谁比你们更差，{demand}？",

    # 理性型
    "我于X月X日购买的{product}，在使用过程中发现{issue}，根据三包规定希望{demand}。",
    "你好，反馈一个问题：{product}{issue}，附有截图，请{demand}处理。",
    "购买的{product}在保修期内出现{issue}，请按合同约定{demand}。",
    "订单号XXXX，{product}{issue}，已保留证据，要求{demand}。",
    "{product}{issue}，请核实情况并尽快{demand}，如有问题可以再沟通。",
]

# 组合更多句式以增加多样性
EMOTION_WORDS = {
    "暴躁型": ["气死了", "烦死了", "受不了了", "太离谱了", "真服了"],
    "委婉型": ["您好", "不好意思", "打扰一下", "麻烦您了", "请问"],
    "焦急型": ["急死了", "等不及了", "马上要", "赶紧", "拜托了"],
    "讽刺型": ["哇", "厉害了", "不错嘛", "绝了", "服了"],
    "理性型": ["你好", "请问", "反馈一下", "麻烦帮忙", "请核实"],
}


def generate_input(emotion, product, issue, demand):
    """根据情绪、商品、问题、诉求生成投诉文本"""
    template = random.choice(SENTENCE_TEMPLATES)
    emotion_word = random.choice(EMOTION_WORDS[emotion])
    text = template.format(
        emotion=emotion_word,
        product=product,
        issue=issue,
        demand=demand
    )
    return text


def generate_output(issues, demands):
    """生成标签化输出"""
    issue_str = "、".join(issues)
    demand_str = "、".join(demands)
    return f"【分类】：{issue_str}\n【核心诉求】：{demand_str}"


def make_key(emotion, product, issue):
    """用于去重的三元组 key"""
    return (emotion, product, issue)


def main():
    random.seed(SEED)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    samples = []
    seen_keys = set()
    seen_inputs = set()

    max_attempts = 2000
    attempt = 0

    while len(samples) < TARGET_COUNT and attempt < max_attempts:
        attempt += 1

        emotion = random.choice(EMOTION_TYPES)
        product = random.choice(PRODUCT_TYPES)
        issue = random.choice(ISSUE_TYPES)
        demand = random.choice(DEMAND_TYPES)

        key = make_key(emotion, product, issue)
        if key in seen_keys:
            continue

        # 30% 的概率添加第二个问题类型（复合投诉）
        extra_issue = None
        if random.random() < 0.3:
            extra_issue = random.choice([i for i in ISSUE_TYPES if i != issue])

        # 20% 的概率添加第二个诉求
        extra_demand = None
        if random.random() < 0.2:
            extra_demand = random.choice([d for d in DEMAND_TYPES if d != demand])

        input_text = generate_input(emotion, product, issue, demand)

        # 文本长度检查
        if len(input_text) < 10 or len(input_text) > 100:
            continue

        # 去重
        input_hash = hashlib.md5(input_text.encode()).hexdigest()
        if input_hash in seen_inputs:
            continue

        issues_list = [issue]
        demands_list = [demand]
        if extra_issue:
            issues_list.append(extra_issue)
        if extra_demand:
            demands_list.append(extra_demand)

        output_text = generate_output(issues_list, demands_list)

        sample = {
            "instruction": "分析投诉文本，归类标签并提取诉求。",
            "input": input_text,
            "output": output_text,
        }

        samples.append(sample)
        seen_keys.add(key)
        seen_inputs.add(input_hash)

    output_path = os.path.join(OUTPUT_DIR, "complaint.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)

    print(f"[投诉分类] 生成完成: {len(samples)} 条")
    print(f"  输出路径: {output_path}")

    return samples


if __name__ == "__main__":
    main()
