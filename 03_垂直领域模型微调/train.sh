#!/bin/bash
# ============================================================
# 训练启动脚本 — 含环境检查、GPU 检测、日志管理
# 用法: bash train.sh [qwen25|deepseek]
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  垂直领域模型微调 — 训练启动${NC}"
echo -e "${GREEN}========================================${NC}"

# ============================================================
# 1. 环境检查
# ============================================================
echo -e "\n${YELLOW}[1/5] 环境检查...${NC}"

# Python 版本
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo -e "${RED}错误: Python 版本 $PYTHON_VERSION 过低，需要 >= 3.10${NC}"
    exit 1
fi
echo -e "  Python: ${GREEN}$PYTHON_VERSION${NC} ✓"

# CUDA
if command -v nvidia-smi &> /dev/null; then
    CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}')
    echo -e "  CUDA:   ${GREEN}$CUDA_VERSION${NC} ✓"
else
    echo -e "${RED}错误: nvidia-smi 未找到，请确认已安装 NVIDIA 驱动${NC}"
    exit 1
fi

# transformers
if python3 -c "import transformers" 2>/dev/null; then
    TF_VERSION=$(python3 -c "import transformers; print(transformers.__version__)")
    echo -e "  transformers: ${GREEN}$TF_VERSION${NC} ✓"
else
    echo -e "${YELLOW}  transformers 未安装，尝试安装...${NC}"
    pip install transformers>=4.40.0
fi

# LLaMA-Factory
if python3 -c "import llamafactory" 2>/dev/null || command -v llamafactory-cli &> /dev/null; then
    echo -e "  LLaMA-Factory: ${GREEN}已安装${NC} ✓"
else
    echo -e "${YELLOW}  LLaMA-Factory 未安装，尝试安装...${NC}"
    pip install llamafactory>=0.7.0
fi

# peft (LoRA 需要)
if python3 -c "import peft" 2>/dev/null; then
    PEFT_VERSION=$(python3 -c "import peft; print(peft.__version__)")
    echo -e "  peft: ${GREEN}$PEFT_VERSION${NC} ✓"
else
    echo -e "${YELLOW}  peft 未安装，尝试安装...${NC}"
    pip install peft>=0.10.0
fi

# ============================================================
# 2. GPU 显存检测
# ============================================================
echo -e "\n${YELLOW}[2/5] GPU 显存检测...${NC}"

GPU_MEM_TOTAL=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1)
GPU_MEM_TOTAL=${GPU_MEM_TOTAL// /}

if [ -z "$GPU_MEM_TOTAL" ]; then
    echo -e "${RED}错误: 无法获取 GPU 显存信息${NC}"
    exit 1
fi

echo -e "  GPU 总显存: ${GREEN}${GPU_MEM_TOTAL}MiB${NC}"

if [ "$GPU_MEM_TOTAL" -lt 8000 ]; then
    echo -e "${RED}错误: 显存不足 8GB，无法运行 7B 模型微调${NC}"
    echo -e "${RED}建议: 使用云 GPU 服务器（A100/4090）${NC}"
    exit 1
elif [ "$GPU_MEM_TOTAL" -lt 16000 ]; then
    echo -e "${YELLOW}警告: 显存不足 16GB，训练可能失败${NC}"
    echo -e "${YELLOW}建议: 降低 batch_size 或使用 QLoRA 量化${NC}"
fi

# ============================================================
# 3. 数据集检查
# ============================================================
echo -e "\n${YELLOW}[3/5] 数据集检查...${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRAIN_DATA="$SCRIPT_DIR/data/cleaned/train_final.json"
DATASET_INFO="$SCRIPT_DIR/data/dataset_info.json"

if [ ! -f "$TRAIN_DATA" ]; then
    echo -e "${RED}错误: 训练数据不存在: $TRAIN_DATA${NC}"
    echo -e "${RED}请先运行: python scripts/generate_complaint.py && python scripts/generate_workorder.py && python scripts/generate_sql.py${NC}"
    echo -e "${RED}然后: python scripts/merge_datasets.py && python scripts/clean_dataset.py && python scripts/split_testset.py${NC}"
    exit 1
fi

TRAIN_COUNT=$(python3 -c "import json; print(len(json.load(open('$TRAIN_DATA'))))")
echo -e "  训练数据: ${GREEN}$TRAIN_COUNT 条${NC} ✓"

if [ ! -f "$DATASET_INFO" ]; then
    echo -e "${RED}错误: dataset_info.json 不存在${NC}"
    exit 1
fi
echo -e "  数据集注册: ${GREEN}✓${NC}"

# ============================================================
# 4. 选择模型
# ============================================================
echo -e "\n${YELLOW}[4/5] 选择模型...${NC}"

MODEL=${1:-qwen25}

case $MODEL in
    qwen25)
        CONFIG="$SCRIPT_DIR/config/train_qwen25_lora.yaml"
        MODEL_NAME="Qwen2.5-7B-Instruct"
        ;;
    deepseek)
        CONFIG="$SCRIPT_DIR/config/train_deepseek_lora.yaml"
        MODEL_NAME="DeepSeek-7B-Chat"
        ;;
    *)
        echo -e "${RED}错误: 未知模型 '$MODEL'，支持: qwen25, deepseek${NC}"
        exit 1
        ;;
esac

if [ ! -f "$CONFIG" ]; then
    echo -e "${RED}错误: 配置文件不存在: $CONFIG${NC}"
    exit 1
fi

echo -e "  模型: ${GREEN}$MODEL_NAME${NC}"
echo -e "  配置: ${GREEN}$CONFIG${NC}"

# ============================================================
# 5. 启动训练
# ============================================================
echo -e "\n${YELLOW}[5/5] 启动训练...${NC}"

# 创建日志目录
mkdir -p "$SCRIPT_DIR/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$SCRIPT_DIR/logs/train_${MODEL}_${TIMESTAMP}.log"
LOSS_FILE="$SCRIPT_DIR/logs/loss_history.jsonl"

echo -e "  日志文件: ${GREEN}$LOG_FILE${NC}"
echo -e "  Loss 记录: ${GREEN}$LOSS_FILE${NC}"
echo ""

# 开始训练
echo "========================================" | tee -a "$LOG_FILE"
echo "训练开始: $(date)" | tee -a "$LOG_FILE"
echo "模型: $MODEL_NAME" | tee -a "$LOG_FILE"
echo "配置: $CONFIG" | tee -a "$LOG_FILE"
echo "GPU: $GPU_MEM_TOTAL MiB" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

cd "$SCRIPT_DIR"
llamafactory-cli train "$CONFIG" 2>&1 | tee -a "$LOG_FILE"

# 提取 loss 历史
echo -e "\n${GREEN}训练完成！${NC}"
echo -e "  输出目录: ${GREEN}output/${MODEL}_lora/${NC}"

# ============================================================
# 完成
# ============================================================
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  训练完成！${NC}"
echo -e "${GREEN}  下一步: python scripts/merge_lora.py --lora_path output/${MODEL}_lora${NC}"
echo -e "${GREEN}========================================${NC}"
