#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON 合规率验证脚本
向微调模型发送测试输入，统计 JSON 输出合规率
用法: python validate_model.py --model_path models/merged_model
"""

import argparse
import json
import os
import re
import sys
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_TEST_FILE = os.path.join(BASE_DIR, "data", "test", "holdout_test.json")
DEFAULT_REPORT_PATH = os.path.join(BASE_DIR, "docs", "validation_report.json")

# 合规检查规则
COMPLAINT_REQUIRED_TAGS = ["【分类】", "【核心诉求】"]
WORKORDER_REQUIRED_FIELDS = ["location", "client_name", "issue", "actions_taken", "assigned_to", "priority"]


def generate_response(model, tokenizer, instruction, input_text, device):
    """使用模型生成回复"""
    # 构造 prompt
    if input_text.strip():
        prompt = f"{instruction}\n\n{input_text}"
    else:
        prompt = instruction

    messages = [{"role": "user", "content": prompt}]

    # 使用 tokenizer 的 chat template（如果有的话）
    if hasattr(tokenizer, "apply_chat_template"):
        try:
            text = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        except Exception:
            text = f"User: {prompt}\nAssistant:"
    else:
        text = f"User: {prompt}\nAssistant:"

    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=1024)
    if device == "cuda":
        inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.1,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )

    # 只取新生成的 tokens
    new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
    response = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
    return response


def check_compliance(output_text, category):
    """
    检查输出是否合规
    返回: (is_compliant, fail_reason)
    """
    # 通用检查：不含代码块标记
    if "```json" in output_text or "```JSON" in output_text:
        return False, "output 含 ```json 代码块标记"
    if "```sql" in output_text or "```SQL" in output_text:
        return False, "output 含 ```sql 代码块标记"

    # 通用检查：不含多余前缀（如 "Here is..."）
    prefix_patterns = [
        r"^(Here|The following|Below|Sure|Of course|Based on)",
        r"^(这是|以下是|根据|按照|好的|没问题)",
    ]
    for pat in prefix_patterns:
        if re.match(pat, output_text, re.IGNORECASE):
            return False, f"output 含多余解释前缀"

    if category == "complaint":
        for tag in COMPLAINT_REQUIRED_TAGS:
            if tag not in output_text:
                return False, f"complaint output 缺少 {tag}"
        return True, None

    elif category == "workorder":
        try:
            data = json.loads(output_text)
            if not isinstance(data, dict):
                return False, "workorder output 不是 JSON 对象"
            for field in WORKORDER_REQUIRED_FIELDS:
                if field not in data:
                    return False, f"workorder JSON 缺少字段: {field}"
            if not isinstance(data.get("actions_taken"), list):
                return False, "workorder actions_taken 不是数组"
            return True, None
        except json.JSONDecodeError as e:
            return False, f"workorder JSON 解析失败: {e}"

    elif category == "nl2sql":
        sql = output_text.strip()
        if not sql.upper().startswith("SELECT"):
            return False, f"nl2sql output 不以 SELECT 开头"
        return True, None

    return False, f"未知场景类型: {category}"


def main():
    parser = argparse.ArgumentParser(description="JSON 合规率验证")
    parser.add_argument("--model_path", type=str, default="models/merged_model",
                        help="合并后模型路径")
    parser.add_argument("--test_file", type=str, default=DEFAULT_TEST_FILE,
                        help="测试集路径")
    parser.add_argument("--output_report", type=str, default=DEFAULT_REPORT_PATH,
                        help="验证报告输出路径")
    parser.add_argument("--max_length", type=int, default=1024,
                        help="输入最大长度")
    args = parser.parse_args()

    # 路径处理
    model_path = os.path.join(BASE_DIR, args.model_path) if not os.path.isabs(args.model_path) else args.model_path
    test_file = args.test_file if os.path.isabs(args.test_file) else os.path.join(BASE_DIR, args.test_file)

    print("=" * 50)
    print("JSON 合规率验证")
    print("=" * 50)
    print(f"  模型路径: {model_path}")
    print(f"  测试文件: {test_file}")
    print()

    # 加载测试数据
    if not os.path.exists(test_file):
        print(f"[ERROR] 测试文件不存在: {test_file}")
        sys.exit(1)

    with open(test_file, "r", encoding="utf-8") as f:
        test_data = json.load(f)

    print(f"  测试样本: {len(test_data)} 条")

    # 加载模型
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n[1/3] 加载模型: {model_path}")
    print(f"  设备: {device}")

    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
        device_map="auto" if device == "cuda" else None,
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    print(f"  模型加载完成，参数量: {model.num_parameters() / 1e9:.2f}B")

    # 逐条验证
    print(f"\n[2/3] 逐条验证...")
    results = []
    passed = 0
    failed = 0

    for i, sample in enumerate(test_data):
        category = sample.get("category", "unknown")
        instruction = sample["instruction"]
        input_text = sample["input"]
        expected = sample["output"]

        # 生成模型输出
        start_time = time.time()
        actual = generate_response(model, tokenizer, instruction, input_text, device)
        gen_time = time.time() - start_time

        # 合规检查
        is_compliant, fail_reason = check_compliance(actual, category)

        if is_compliant:
            passed += 1
            status = "✓ PASS"
        else:
            failed += 1
            status = f"✗ FAIL: {fail_reason}"

        results.append({
            "index": i + 1,
            "category": category,
            "input": input_text[:100] + "..." if len(input_text) > 100 else input_text,
            "expected_output": expected[:150],
            "actual_output": actual[:150],
            "passed": is_compliant,
            "fail_reason": fail_reason,
            "generation_time_ms": round(gen_time * 1000, 1),
        })

        print(f"  [{i+1:2d}/{len(test_data)}] {status}")

    # 汇总
    total = len(test_data)
    compliance_rate = (passed / total * 100) if total > 0 else 0

    print(f"\n[3/3] 生成报告...")
    print()
    print("=" * 50)
    print(f"  总测试数: {total}")
    print(f"  通过:     {passed}")
    print(f"  失败:     {failed}")
    print(f"  合规率:   {compliance_rate:.2f}%")
    print("=" * 50)

    # 失败分析
    failure_analysis = {}
    if failed > 0:
        print("\n失败案例分析:")
        for r in results:
            if not r["passed"]:
                reason = r["fail_reason"]
                failure_analysis[reason] = failure_analysis.get(reason, 0) + 1
                print(f"  [{r['index']}] [{r['category']}] {reason}")
                print(f"       输入: {r['input'][:60]}...")
                print(f"       输出: {r['actual_output'][:80]}...")
                print()

    if compliance_rate < 100:
        print("\n调整建议:")
        print("  1. 检查失败案例的 pattern，是否是特定场景的问题")
        print("  2. 如果是格式问题，增加对应场景的训练数据")
        print("  3. 降低 temperature 到 0.01 提高输出确定性")
        print("  4. 检查训练数据质量，确保格式一致")

    # 保存报告
    report = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "compliance_rate": f"{compliance_rate:.2f}%",
        "model_path": model_path,
        "test_file": test_file,
        "details": results,
        "failure_analysis": failure_analysis,
    }

    report_path = args.output_report if os.path.isabs(args.output_report) else os.path.join(BASE_DIR, args.output_report)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n报告已保存: {report_path}")


if __name__ == "__main__":
    main()
