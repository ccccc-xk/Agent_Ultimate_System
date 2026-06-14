# 03 垂直领域模型微调

AI 全栈生态第三阶段——解决公共大模型"说话不守规矩、格式不稳定"的问题，通过 SFT 微调让模型 100% 稳定输出合法 JSON。

## 技术栈

| 层级 | 技术 |
|------|------|
| 语言 | Python 3.10+ |
| 微调框架 | LLaMA-Factory + LoRA |
| 基座模型 | Qwen2.5-7B-Instruct / DeepSeek-7B-Chat |
| 部署 | vLLM（OpenAI 兼容 API） |
| 容器化 | Docker |
| 运行环境 | Linux (Ubuntu) + CUDA |

## 快速开始

### 1. 生成训练数据

```bash
python scripts/generate_complaint.py    # 投诉分类归因：60 条
python scripts/generate_workorder.py    # 口语化工单提取：60 条
python scripts/generate_sql.py          # 自然语言转SQL：60 条
python scripts/merge_datasets.py        # 合并
python scripts/clean_dataset.py         # 清洗
python scripts/split_testset.py         # 划分训练集/测试集
```

### 2. 启动训练

```bash
bash train.sh qwen25    # 或 bash train.sh deepseek
```

### 3. 合并模型

```bash
python scripts/merge_lora.py --lora_path output/qwen25_lora
```

### 4. 验证合规率

```bash
python scripts/validate_model.py --model_path models/merged_model
```

### 5. 部署 API

```bash
bash deploy/start_vllm.sh models/merged_model your-api-key
```

## 目录结构

```
03_垂直领域模型微调/
├── data/
│   ├── raw/                    # 原始生成数据
│   ├── cleaned/                # 清洗后训练集
│   ├── test/                   # Holdout 验证集（20 条）
│   └── dataset_info.json       # LLaMA-Factory 数据集注册
├── scripts/
│   ├── generate_complaint.py   # 场景一：投诉分类归因数据生成
│   ├── generate_workorder.py   # 场景二：口语化工单提取数据生成
│   ├── generate_sql.py         # 场景三：自然语言转SQL数据生成
│   ├── merge_datasets.py       # 三场景合并
│   ├── clean_dataset.py        # 数据清洗（去重/校验/过滤）
│   ├── split_testset.py        # 测试集划分
│   ├── merge_lora.py           # LoRA 权重合并
│   └── validate_model.py       # JSON 合规率验证
├── config/
│   ├── train_qwen25_lora.yaml  # Qwen2.5-7B 训练配置
│   └── train_deepseek_lora.yaml# DeepSeek-7B 训练配置
├── deploy/
│   ├── start_vllm.sh           # vLLM 启动脚本
│   ├── Dockerfile              # 容器化部署
│   └── benchmark.py            # 并发压测脚本
├── docs/
│   ├── training_report.md      # 训练报告模板
│   └── 部署文档.md     # 部署文档
├── train.sh                    # 训练启动脚本（含环境检查）
├── requirements.txt            # Python 依赖
└── README.md                   # 本文件
```

## 三大业务场景

| 场景 | 输入 | 输出格式 | 示例 |
|------|------|----------|------|
| 投诉分类归因 | 投诉文本 | `【分类】：X\n【核心诉求】：Y` | "衣服线头全开了，退钱！" → 质量问题 / 退款 |
| 口语化工单提取 | 口语化报修文本 | 严格 JSON | "3楼空调不制冷" → {location, issue, priority...} |
| 自然语言转SQL | 管理查询问题 | SELECT SQL | "上月销售额最高的产品" → SELECT... |

## 训练参数

| 参数 | 值 |
|------|-----|
| LoRA rank / alpha | 16 / 32 |
| 学习率 | 2e-4 |
| 训练轮数 | 3 |
| Batch Size | 4 × 4 (gradient_accumulation) = 16 |
| 精度 | bf16 |

## 服务器要求

- **GPU**: ≥ 16GB 显存（推荐 A100 40GB / RTX 4090）
- **CUDA**: ≥ 12.1
- **内存**: ≥ 32GB
- **磁盘**: ≥ 100GB

详细部署步骤见 [部署文档.md](docs/部署文档.md)。

## 常见问题

**Q: 本地 6GB 显卡能训练吗？**
A: 不能直接训练。代码写好后拿到云 GPU 服务器（AutoDL/阿里云 A100）上执行。

**Q: 为什么用模板生成数据而不是调 LLM API？**
A: 模板方式零成本、可复现、无外部依赖。训练数据量（150+ 条）用模板足够覆盖格式模式。

**Q: 合规率不达标怎么办？**
A: 运行 `validate_model.py` 查看失败分析报告，根据失败类型补充对应场景的训练数据，重新训练。

