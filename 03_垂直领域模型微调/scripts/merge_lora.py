#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LoRA 权重合并到基座模型
用法: python merge_lora.py --base_model Qwen/Qwen2.5-7B-Instruct --lora_path output/qwen25_lora --output_path models/merged_model
"""

import argparse
import os
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def main():
    parser = argparse.ArgumentParser(description="将 LoRA 权重合并到基座模型")
    parser.add_argument("--base_model", type=str, default="Qwen/Qwen2.5-7B-Instruct",
                        help="基座模型路径或 HuggingFace ID")
    parser.add_argument("--lora_path", type=str, default="output/qwen25_lora",
                        help="LoRA adapter 路径")
    parser.add_argument("--output_path", type=str, default="models/merged_model",
                        help="合并后模型保存路径")
    parser.add_argument("--use_fast_tokenizer", action="store_true", default=True,
                        help="使用 fast tokenizer")
    args = parser.parse_args()

    # 路径处理
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    lora_path = os.path.join(base_dir, args.lora_path) if not os.path.isabs(args.lora_path) else args.lora_path
    output_path = os.path.join(base_dir, args.output_path) if not os.path.isabs(args.output_path) else args.output_path

    print("=" * 50)
    print("LoRA 权重合并")
    print("=" * 50)
    print(f"  基座模型: {args.base_model}")
    print(f"  LoRA 路径: {lora_path}")
    print(f"  输出路径: {output_path}")
    print()

    # 检查 LoRA 路径
    if not os.path.exists(lora_path):
        print(f"[ERROR] LoRA 路径不存在: {lora_path}")
        sys.exit(1)

    # 检测 GPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if device == "cuda" else torch.float32
    print(f"  设备: {device}")
    print(f"  精度: {dtype}")
    print()

    # 加载基座模型
    print("[1/4] 加载基座模型...")
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=dtype,
        device_map="auto" if device == "cuda" else None,
        trust_remote_code=True,
    )
    print(f"  参数量: {model.num_parameters() / 1e9:.2f}B")

    # 加载 LoRA adapter
    print("[2/4] 加载 LoRA adapter...")
    from peft import PeftModel
    model = PeftModel.from_pretrained(model, lora_path)
    print("  LoRA adapter 加载完成")

    # 合并权重
    print("[3/4] 合并 LoRA 权重...")
    model = model.merge_and_unload()
    print("  合并完成")

    # 保存
    print(f"[4/4] 保存合并模型到: {output_path}")
    os.makedirs(output_path, exist_ok=True)
    model.save_pretrained(output_path)

    # 保存 tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        args.base_model,
        trust_remote_code=True,
    )
    tokenizer.save_pretrained(output_path)

    # 统计
    total_size = 0
    for f in os.listdir(output_path):
        fp = os.path.join(output_path, f)
        if os.path.isfile(fp):
            total_size += os.path.getsize(fp)

    print()
    print("=" * 50)
    print(f"合并完成！")
    print(f"  输出目录: {output_path}")
    print(f"  文件大小: {total_size / 1e9:.2f} GB")
    print(f"  下一步: python scripts/validate_model.py --model_path {args.output_path}")
    print("=" * 50)


if __name__ == "__main__":
    main()
