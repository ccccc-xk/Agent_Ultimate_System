#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场景二：口语化工单提取 — SFT 训练数据生成
instruction: "从口语化文本中提取工单信息，返回纯JSON。"
output 为严格 JSON: {location, client_name, issue, actions_taken:[], assigned_to, priority}
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

LOCATIONS = [
    "3楼301会议室", "5楼茶水间", "1楼大厅", "地下车库B2层",
    "2楼财务部办公室", "4楼研发部工位区", "6楼天台",
    "8楼总经理办公室", "1楼前台接待区", "负1楼配电房"
]

CLIENTS = [
    "张经理", "李总", "王姐", "小刘", "赵工",
    "陈主任", "周科长", "孙部长", "吴助理", "钱会计"
]

EQUIPMENT_TYPES = ["空调", "投影仪", "打印机", "饮水机", "门禁", "WiFi", "电梯", "监控摄像头"]

FAULTS = ["不制冷", "打不开", "卡纸", "漏水", "无法识别", "连不上", "异响", "画面模糊"]

# 设备 → 故障 合理映射
EQUIPMENT_FAULT_MAP = {
    "空调": ["不制冷", "异响", "漏水", "打不开"],
    "投影仪": ["打不开", "画面模糊", "无法识别"],
    "打印机": ["卡纸", "打不开", "画面模糊"],
    "饮水机": ["不制冷", "漏水", "异响"],
    "门禁": ["无法识别", "打不开"],
    "WiFi": ["连不上", "信号弱"],
    "电梯": ["打不开", "异响"],
    "监控摄像头": ["画面模糊", "打不开", "连不上"],
}

PRIORITIES = ["高", "中", "低"]

ACTIONS_POOL = [
    "已检查电源", "已重启设备", "已联系厂家", "已断电等待",
    "已拍照记录", "已通知物业", "已检查线路", "已清洁滤网",
    "已更换耗材", "已检查网络", "已重置密码", "已加注制冷剂"
]

# 设备 → 维修人员映射
EQUIPMENT_ASSIGN_MAP = {
    "空调": "维修部李工",
    "投影仪": "IT部小陈",
    "打印机": "行政部小王",
    "饮水机": "物业部老张",
    "门禁": "安保部大刘",
    "WiFi": "IT部小陈",
    "电梯": "维保单位周师傅",
    "监控摄像头": "安保部大刘",
}

# 口语化句式模板
SENTENCE_TEMPLATES = [
    "{client}打电话说{location}的{equipment}{fault}了",
    "{location}那个{equipment}{fault}了，{client}反映的",
    "刚接到{client}的报修，{location}的{equipment}{fault}",
    "{client}说{location}的{equipment}有问题，{fault}",
    "紧急！{client}反映{location}的{equipment}{fault}，需要马上处理",
    "{location}的{equipment}{fault}了，{client}催了好几次了",
    "帮{client}报个修，{location}那个{equipment}一直{fault}",
    "{client}说{location}那边{equipment}{fault}了，看看谁去处理下",
    "{location}出了点状况，{client}反馈{equipment}{fault}",
    "{client}今天过来说{location}的{equipment}{fault}，挺着急的",
    "刚才{client}来报修，{location}的{equipment}{fault}了，影响办公",
    "{client}发消息说{location}的{equipment}{fault}，要尽快处理",
]


def generate_input(client, location, equipment, fault):
    """生成口语化报修文本"""
    template = random.choice(SENTENCE_TEMPLATES)
    text = template.format(
        client=client,
        location=location,
        equipment=equipment,
        fault=fault
    )
    return text


def generate_output(location, client_name, issue, actions_taken, assigned_to, priority):
    """生成严格 JSON 格式输出"""
    data = {
        "location": location,
        "client_name": client_name,
        "issue": issue,
        "actions_taken": actions_taken,
        "assigned_to": assigned_to,
        "priority": priority
    }
    return json.dumps(data, ensure_ascii=False)


def main():
    random.seed(SEED)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    samples = []
    seen_inputs = set()

    max_attempts = 2000
    attempt = 0

    while len(samples) < TARGET_COUNT and attempt < max_attempts:
        attempt += 1

        client = random.choice(CLIENTS)
        location = random.choice(LOCATIONS)
        equipment = random.choice(EQUIPMENT_TYPES)
        # 从设备的合理故障列表中选择
        fault = random.choice(EQUIPMENT_FAULT_MAP[equipment])
        priority = random.choice(PRIORITIES)
        assigned_to = EQUIPMENT_ASSIGN_MAP[equipment]

        # 随机选择 1-3 项已采取措施
        num_actions = random.randint(1, 3)
        actions = random.sample(ACTIONS_POOL, num_actions)

        input_text = generate_input(client, location, equipment, fault)

        # 去重
        input_hash = hashlib.md5(input_text.encode()).hexdigest()
        if input_hash in seen_inputs:
            continue

        issue = f"{equipment}{fault}"
        output_text = generate_output(location, client, issue, actions, assigned_to, priority)

        sample = {
            "instruction": "从口语化文本中提取工单信息，返回纯JSON。",
            "input": input_text,
            "output": output_text,
        }

        # 验证 output 是合法 JSON
        try:
            json.loads(output_text)
        except json.JSONDecodeError:
            continue

        samples.append(sample)
        seen_inputs.add(input_hash)

    output_path = os.path.join(OUTPUT_DIR, "workorder.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)

    print(f"[工单提取] 生成完成: {len(samples)} 条")
    print(f"  输出路径: {output_path}")

    return samples


if __name__ == "__main__":
    main()
