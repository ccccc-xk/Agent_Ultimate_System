# 03 垂直领域模型微调 — 实施计划

> 目标：通过 SFT 微调，让大模型 100% 稳定输出合法 JSON，解决"格式不稳定"问题。

---

## 项目结构

```
03_垂直领域模型微调/
├── data/
│   ├── raw/                        # 原始生成数据（3个场景JSON文件）
│   ├── cleaned/                    # 清洗后训练数据
│   ├── test/                       # Holdout验证集（20条，不出现在训练集中）
│   └── dataset_info.json           # LLaMA-Factory 数据集注册文件
├── scripts/
│   ├── generate_complaint.py       # 场景一：投诉分类归因数据生成
│   ├── generate_workorder.py       # 场景二：口语化工单提取数据生成
│   ├── generate_sql.py             # 场景三：自然语言转SQL数据生成
│   ├── merge_datasets.py           # 合并三场景数据集
│   ├── clean_dataset.py            # 数据清洗（去重/校验/过滤）
│   ├── split_testset.py            # 划分Holdout测试集
│   ├── merge_lora.py               # LoRA权重合并到基座模型
│   └── validate_model.py           # JSON合规率验证脚本
├── config/
│   ├── train_qwen25_lora.yaml      # Qwen2.5-7B LoRA训练配置
│   └── train_deepseek_lora.yaml    # DeepSeek-7B LoRA训练配置
├── deploy/
│   ├── start_vllm.sh               # vLLM服务启动脚本
│   ├── Dockerfile                  # Docker镜像构建
│   └── benchmark.py                # 并发压测脚本
├── docs/
│   ├── plan.md                     # 本文件
│   ├── training_report.md          # 训练报告模板
│   └── deployment_guide.md         # 部署文档
├── train.sh                        # 训练启动脚本（含环境检查）
├── requirements.txt                # Python依赖
└── README.md                       # 项目总文档
```

---

## 第一步：高质量 SFT 数据集构建

### 1.1 数据生成脚本

采用 Python 模板 + 随机组合方式，零外部 API 依赖，立即可运行。

#### 场景一：投诉分类归因（`scripts/generate_complaint.py`）

- **instruction**：固定为 `"分析投诉文本，归类标签并提取诉求。"`
- **input 模板库**：预设 30+ 个投诉文本模板，覆盖：
  - 暴躁型投诉（"气死了"、"退钱"、"垃圾"等情绪词）
  - 委婉型投诉（"不太满意"、"希望能改进"等温和表达）
  - 复合型投诉（同时涉及多个问题）
  - 变量槽位：商品类型（衣服/手机/食品/家电等）、问题描述、情绪强度
- **output 格式**：
  ```
  【分类】：质量问题/物流延迟/客服态度（可多选）
  【核心诉求】：退款/赔偿/换货/道歉
  ```
- **生成逻辑**：随机组合 情绪模板 × 商品类型 × 问题类型 × 诉求类型，确保不重复
- **生成数量**：60 条（含 10 条作为holdout候选）

#### 场景二：口语化工单提取（`scripts/generate_workorder.py`）

- **instruction**：固定为 `"从口语化文本中提取工单信息，返回纯JSON。"`
- **input 模板库**：预设 30+ 个口语化报修/汇报文本模板，覆盖：
  - 报修场景（"3楼那个空调又不制冷了"）
  - 设备故障（"会议室投影仪打不开了"）
  - 网络问题（"5楼WiFi连不上了"）
  - 变量槽位：楼栋/房间、设备类型、故障描述、报修人
- **output 格式**（严格JSON）：
  ```json
  {
    "location": "3楼301会议室",
    "client_name": "张经理",
    "issue": "空调不制冷",
    "actions_taken": ["已检查电源", "已重启设备"],
    "assigned_to": "维修部李工",
    "priority": "高"
  }
  ```
- **生成逻辑**：随机组合 位置 × 人员 × 设备 × 故障 × 优先级，actions_taken 从预设池随机抽取 1-3 项
- **生成数量**：60 条

#### 场景三：自然语言转SQL（`scripts/generate_sql.py`）

- **instruction**：固定为 `"将自然语言问题转换为MySQL查询语句。"`
- **input 模板库**：预设 25+ 个管理查询模板，覆盖：
  - 统计查询（"查一下上个月销售额最高的产品"）
  - 筛选查询（"找出所有超过30天未付款的订单"）
  - 排名查询（"销售部业绩排名前5的员工"）
  - 聚合查询（"各部门的平均薪资是多少"）
  - 变量槽位：表名、字段名、时间范围、排序方式、聚合函数
- **output 格式**：标准 SELECT SQL，带表名、WHERE、ORDER BY、LIMIT 等
- **涉及表结构**：预设 5 张业务表（orders, products, employees, departments, customers）
- **生成数量**：60 条

#### 数据合并（`scripts/merge_datasets.py`）

- 将三个场景的 JSON 文件合并为一个统一的 JSON 数组
- 每条记录添加 `category` 字段标记来源场景
- 输出：`data/raw/train_all.json`

### 1.2 数据清洗脚本（`scripts/clean_dataset.py`）

| 清洗步骤 | 规则 |
|---|---|
| 去重 | 基于 instruction+input 精确去重；基于 input 文本相似度（编辑距离 < 阈值）模糊去重 |
| 格式校验 | 必须包含 instruction/input/output 三个字段且非空 |
| 长度过滤 | input ≥ 10字符，output ≥ 5字符，排除过短无效条目 |
| JSON校验 | 场景二的 output 必须是合法 JSON |
| SQL校验 | 场景三的 output 必须以 SELECT 开头 |
| 输出编码 | UTF-8 无 BOM |

- 输出：`data/cleaned/train_clean.json`
- 输出清洗报告：总数、去重数、过滤数、各场景分布

### 1.3 测试集划分（`scripts/split_testset.py`）

- 从清洗后数据中按场景抽取 20 条（场景一7条、场景二7条、场景三6条）
- 抽取的条目从训练集中移除
- 输出：
  - `data/cleaned/train_final.json`（训练集，约130+条）
  - `data/test/holdout_test.json`（验证集，20条）

### 1.4 LLaMA-Factory 数据集注册（`data/dataset_info.json`）

- 注册数据集路径和格式为 LLaMA-Factory 可识别的 alpaca 格式
- 字段映射：instruction→instruction, input→input, output→output

---

## 第二步：LLaMA-Factory 微调配置与训练

### 2.1 训练配置文件

生成两套 YAML 配置：

**`config/train_qwen25_lora.yaml`**（Qwen2.5-7B）

| 参数 | 值 | 说明 |
|---|---|---|
| model_name_or_path | Qwen/Qwen2.5-7B-Instruct | HuggingFace模型ID |
| stage | sft | 监督微调 |
| finetuning_type | lora | LoRA微调 |
| lora_rank | 16 | LoRA秩 |
| lora_alpha | 32 | LoRA缩放系数 |
| lora_target | q_proj,v_proj | 目标模块 |
| learning_rate | 2e-4 | 学习率 |
| num_train_epochs | 3 | 训练轮数 |
| per_device_train_batch_size | 4 | 单卡batch size |
| gradient_accumulation_steps | 4 | 梯度累积（等效batch=16） |
| bf16 | true | 混合精度 |
| logging_steps | 10 | 日志间隔 |
| save_steps | 50 | checkpoint间隔 |
| output_dir | output/qwen25_lora | 输出目录 |

**`config/train_deepseek_lora.yaml`**（DeepSeek-7B）
- 参数同上，仅替换 model_name_or_path 为 deepseek-ai/deepseek-llm-7b-chat

### 2.2 训练启动脚本（`train.sh`）

脚本执行流程：

```
1. 环境检查
   ├── Python ≥ 3.10
   ├── CUDA 版本 ≥ 11.8
   ├── transformers 版本
   └── LLaMA-Factory 已安装

2. GPU 检测
   ├── nvidia-smi 获取显存
   ├── 显存 < 16GB → 警告并建议用 Qwen2.5-7B（更省显存）
   └── 显存 < 8GB → 报错退出

3. 数据集检查
   ├── train_final.json 存在性
   └── dataset_info.json 注册

4. 启动训练
   ├── llamafactory-cli train config/train_<model>.yaml
   ├── 日志输出到 logs/train_<timestamp>.log
   └── 后台监控 loss 写入 logs/loss_history.jsonl

5. 训练完成
   ├── 输出最终 checkpoint 路径
   └── 生成 loss 曲线数据
```

---

## 第三步：模型合并与格式固化验证

### 3.1 LoRA 权重合并（`scripts/merge_lora.py`）

- 使用 transformers + peft 库
- 加载基座模型 → 加载 LoRA adapter → merge_and_unload → 保存完整模型
- 输出路径：`models/merged_<model_name>/`
- 同时保存 tokenizer

### 3.2 JSON 合规率验证（`scripts/validate_model.py`）

**验证流程**：

```
1. 加载合并后模型（transformers + 自动设备映射）
2. 读取 holdout_test.json（20条测试数据）
3. 对每条测试：
   ├── 构造 prompt（instruction + input）
   ├── 模型推理生成 output
   └── 合规检查：
       ├── 是合法 JSON（json.loads 不报错）
       ├── 不含 ```json 标记
       ├── 不含多余解释文字（output 以 { 或 【 开头）
       └── 字段完整性（场景二检查必需字段）
4. 统计合规率
5. 输出验证报告
```

**合规标准**：
- 场景一：以 `【分类】` 开头，包含 `【核心诉求】`
- 场景二：是合法 JSON，包含 location/issue/priority 等字段
- 场景三：以 `SELECT` 开头，是合法 SQL 语法

**不达标处理**：
- 合规率 < 100% 时，输出失败 case 分析报告
- 标注失败类型：格式错误/字段缺失/多余文字/其他
- 建议数据集调整方向

**输出**：`docs/validation_report.json`（每条测试的输入、输出、合规状态、失败原因）

---

## 第四步：vLLM 部署为 API 服务

### 4.1 vLLM 启动脚本（`deploy/start_vllm.sh`）

```bash
python -m vllm.entrypoints.openai.api_server \
    --model /path/to/merged_model \
    --served-model-name vertical-sft-model \
    --tensor-parallel-size 1 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9 \
    --port 8000 \
    --api-key your-secret-key
```

- 兼容 OpenAI API：`/v1/chat/completions`
- 支持 tensor-parallel 多卡部署（自动检测GPU数量）
- 内置健康检查端点

### 4.2 Dockerfile（`deploy/Dockerfile`）

```dockerfile
FROM vllm/vllm-openai:latest
COPY models/merged_model /app/model
COPY deploy/start_vllm.sh /app/
EXPOSE 8000
HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1
CMD ["/app/start_vllm.sh"]
```

### 4.3 压测脚本（`deploy/benchmark.py`）

- 基于 aiohttp 实现异步并发
- 参数：50 并发、共 500 请求
- 统计指标：
  - QPS（每秒查询数）
  - P50 / P95 / P99 延迟
  - 错误率
  - Token 吞吐量
- 输出报告：`docs/benchmark_report.json`

---

## 第五步：文档与交付物

### 5.1 训练报告（`docs/training_report.md`）

- 数据量统计：各场景条数、清洗前后对比
- 训练超参数清单
- Loss 曲线数据（可选：生成 matplotlib 图表脚本）
- 验证结果：合规率、失败分析

### 5.2 部署文档（`docs/deployment_guide.md`）

- 服务器环境要求：Ubuntu 22.04+, CUDA 12.1+, Python 3.10+
- 显存需求：7B模型单卡 ≥ 16GB（推荐 A100/4090）
- 安装步骤（含 LLaMA-Factory、vLLM 安装命令）
- 训练启动命令
- 部署启动命令
- API 调用示例（curl + Python requests）

### 5.3 API 调用示例

**curl 示例**：
```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"model":"vertical-sft-model","messages":[{"role":"user","content":"分析投诉文本，归类标签并提取诉求。\n衣服线头全开了，退钱！"}]}'
```

**Python 示例**：
```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000/v1", api_key="your-secret-key")
response = client.chat.completions.create(
    model="vertical-sft-model",
    messages=[{"role":"user","content":"分析投诉文本，归类标签并提取诉求。\n衣服线头全开了，退钱！"}]
)
```

### 5.4 README.md

- 项目简介与目标
- 快速开始（数据生成 → 训练 → 验证 → 部署 四步）
- 目录结构说明
- 技术栈说明
- 常见问题

---

## 文件交付清单

| 步骤 | 文件 | 说明 |
|---|---|---|
| 1 | `scripts/generate_complaint.py` | 投诉分类数据生成 |
| 1 | `scripts/generate_workorder.py` | 工单提取数据生成 |
| 1 | `scripts/generate_sql.py` | NL2SQL数据生成 |
| 1 | `scripts/merge_datasets.py` | 数据合并 |
| 1 | `scripts/clean_dataset.py` | 数据清洗 |
| 1 | `scripts/split_testset.py` | 测试集划分 |
| 1 | `data/dataset_info.json` | LLaMA-Factory注册 |
| 2 | `config/train_qwen25_lora.yaml` | Qwen2.5训练配置 |
| 2 | `config/train_deepseek_lora.yaml` | DeepSeek训练配置 |
| 2 | `train.sh` | 训练启动脚本 |
| 3 | `scripts/merge_lora.py` | LoRA合并 |
| 3 | `scripts/validate_model.py` | 合规率验证 |
| 4 | `deploy/start_vllm.sh` | vLLM启动 |
| 4 | `deploy/Dockerfile` | Docker构建 |
| 4 | `deploy/benchmark.py` | 压测脚本 |
| 5 | `docs/training_report.md` | 训练报告 |
| 5 | `docs/deployment_guide.md` | 部署文档 |
| 5 | `README.md` | 项目总文档 |
| — | `requirements.txt` | Python依赖 |

共 19 个文件，覆盖从数据生成到部署上线的完整链路。
