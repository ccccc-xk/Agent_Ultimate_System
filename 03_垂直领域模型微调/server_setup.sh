#!/bin/bash
# ============================================================
# 服务器一键部署脚本
# 用法: bash server_setup.sh [qwen25|deepseek]
#
# 在新租的 GPU 服务器上执行：
#   1. 上传整个项目目录到服务器
#   2. cd 到项目目录
#   3. 执行: bash server_setup.sh qwen25
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

MODEL=${1:-qwen25}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  垂直领域模型微调 — 服务器一键部署${NC}"
echo -e "${CYAN}============================================${NC}"

# ============================================================
# 第 1 步：环境检查
# ============================================================
echo -e "\n${YELLOW}[1/6] 环境检查...${NC}"

# Python
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "  Python: ${GREEN}$PYTHON_VERSION${NC}"

# CUDA
if ! command -v nvidia-smi &> /dev/null; then
    echo -e "${RED}错误: nvidia-smi 未找到${NC}"
    exit 1
fi

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)
GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
GPU_MEM=${GPU_MEM// /}
CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}')

echo -e "  GPU: ${GREEN}$GPU_NAME${NC}"
echo -e "  显存: ${GREEN}${GPU_MEM}MiB${NC}"
echo -e "  CUDA: ${GREEN}$CUDA_VERSION${NC}"

if [ "$GPU_MEM" -lt 16000 ]; then
    echo -e "${YELLOW}警告: 显存不足 16GB，建议使用 QLoRA 量化训练${NC}"
fi

# ============================================================
# 第 2 步：安装依赖
# ============================================================
echo -e "\n${YELLOW}[2/6] 安装依赖...${NC}"

pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ 2>/dev/null || true
pip config set global.trusted-host mirrors.aliyun.com 2>/dev/null || true

cd "$SCRIPT_DIR"
pip install -r requirements.txt --quiet 2>&1 | tail -5

echo -e "  依赖安装 ${GREEN}完成${NC}"

# ============================================================
# 第 3 步：设置 HuggingFace 镜像
# ============================================================
echo -e "\n${YELLOW}[3/6] 配置 HuggingFace 镜像...${NC}"

export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/root/.cache/huggingface
echo -e "  HF_ENDPOINT: ${GREEN}$HF_ENDPOINT${NC}"

# 检查 hf CLI
if command -v hf &> /dev/null; then
    echo -e "  hf CLI: ${GREEN}$(hf --version)${NC}"
elif command -v huggingface-cli &> /dev/null; then
    echo -e "  huggingface-cli: ${GREEN}可用${NC}"
else
    echo -e "${YELLOW}  安装 huggingface_hub[cli]...${NC}"
    pip install "huggingface_hub[cli]" --quiet
fi

# ============================================================
# 第 4 步：下载模型
# ============================================================
echo -e "\n${YELLOW}[4/6] 下载模型...${NC}"

case $MODEL in
    qwen25)
        HF_MODEL="Qwen/Qwen2.5-7B-Instruct"
        LOCAL_MODEL="/root/models/Qwen2.5-7B-Instruct"
        ;;
    deepseek)
        HF_MODEL="deepseek-ai/deepseek-llm-7b-chat"
        LOCAL_MODEL="/root/models/deepseek-llm-7b-chat"
        ;;
    *)
        echo -e "${RED}错误: 未知模型 '$MODEL'，支持: qwen25, deepseek${NC}"
        exit 1
        ;;
esac

echo -e "  模型: ${GREEN}$HF_MODEL${NC}"
echo -e "  本地路径: ${GREEN}$LOCAL_MODEL${NC}"

if [ -d "$LOCAL_MODEL" ] && [ -f "$LOCAL_MODEL/config.json" ]; then
    echo -e "  ${GREEN}模型已存在，跳过下载${NC}"
else
    mkdir -p "$LOCAL_MODEL"
    echo -e "  开始下载（使用 hf-mirror.com 加速）..."
    echo -e "  ${YELLOW}模型约 15GB，下载时间取决于网速${NC}"

    # 使用 hf download（新版 CLI）
    if command -v hf &> /dev/null; then
        hf download "$HF_MODEL" \
            --local-dir "$LOCAL_MODEL" \
            --endpoint "$HF_ENDPOINT" \
            2>&1 | while IFS= read -r line; do
                if [[ "$line" == *"%"* ]] || [[ "$line" == *"Downloading"* ]] || [[ "$line" == *"Download"* ]]; then
                    echo -ne "\r  下载中: $line"
                fi
            done
    else
        # 旧版 CLI 兼容
        huggingface-cli download "$HF_MODEL" \
            --local_dir "$LOCAL_MODEL" \
            --resume-download \
            --endpoint "$HF_ENDPOINT"
    fi

    if [ -f "$LOCAL_MODEL/config.json" ]; then
        echo -e "\n  ${GREEN}模型下载完成${NC}"
    else
        echo -e "\n  ${RED}模型下载可能不完整，请检查 $LOCAL_MODEL${NC}"
        echo -e "  ${YELLOW}手动下载命令:${NC}"
        echo -e "  hf download $HF_MODEL --local-dir $LOCAL_MODEL --endpoint https://hf-mirror.com"
        exit 1
    fi
fi

# 更新配置文件中的模型路径
CONFIG_FILE="$SCRIPT_DIR/config/train_${MODEL}_lora.yaml"
if [ -f "$CONFIG_FILE" ]; then
    sed -i "s|model_name_or_path:.*|model_name_or_path: $LOCAL_MODEL|" "$CONFIG_FILE"
    echo -e "  配置文件已更新模型路径: ${GREEN}$CONFIG_FILE${NC}"
fi

# ============================================================
# 第 5 步：验证数据集
# ============================================================
echo -e "\n${YELLOW}[5/6] 验证数据集...${NC}"

TRAIN_DATA="$SCRIPT_DIR/data/cleaned/train_final.json"
TEST_DATA="$SCRIPT_DIR/data/test/holdout_test.json"

if [ -f "$TRAIN_DATA" ]; then
    TRAIN_COUNT=$(python3 -c "import json; print(len(json.load(open('$TRAIN_DATA'))))")
    echo -e "  训练集: ${GREEN}$TRAIN_COUNT 条${NC}"
else
    echo -e "${RED}错误: 训练数据不存在 $TRAIN_DATA${NC}"
    exit 1
fi

if [ -f "$TEST_DATA" ]; then
    TEST_COUNT=$(python3 -c "import json; print(len(json.load(open('$TEST_DATA'))))")
    echo -e "  测试集: ${GREEN}$TEST_COUNT 条${NC}"
else
    echo -e "${YELLOW}警告: 测试集不存在${NC}"
fi

# ============================================================
# 第 6 步：启动训练
# ============================================================
echo -e "\n${YELLOW}[6/6] 启动训练...${NC}"

CONFIG="$SCRIPT_DIR/config/train_${MODEL}_lora.yaml"
mkdir -p "$SCRIPT_DIR/logs"
mkdir -p "$SCRIPT_DIR/output"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$SCRIPT_DIR/logs/train_${MODEL}_${TIMESTAMP}.log"

echo -e "  配置: ${GREEN}$CONFIG${NC}"
echo -e "  日志: ${GREEN}$LOG_FILE${NC}"
echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  开始训练...${NC}"
echo -e "${CYAN}  训练期间可以开另一个 SSH 窗口监控:${NC}"
echo -e "${CYAN}  tail -f $LOG_FILE${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

cd "$SCRIPT_DIR"
llamafactory-cli train "$CONFIG" 2>&1 | tee -a "$LOG_FILE"

# 训练完成后
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  训练完成！${NC}"
echo -e "${GREEN}  LoRA 权重: output/${MODEL}_lora/${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "下一步操作："
echo -e "  1. 合并模型:  python3 scripts/merge_lora.py --lora_path output/${MODEL}_lora --output_path /root/models/merged_${MODEL}"
echo -e "  2. 验证模型:  python3 scripts/validate_model.py --model_path /root/models/merged_${MODEL}"
echo -e "  3. 部署 API:  bash deploy/start_vllm.sh /root/models/merged_${MODEL}"
