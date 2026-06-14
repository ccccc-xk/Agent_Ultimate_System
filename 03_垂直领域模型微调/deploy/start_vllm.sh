#!/bin/bash
# ============================================================
# vLLM OpenAI 兼容 API 启动脚本
# 用法: bash start_vllm.sh [模型路径] [API Key] [TP Size]
# ============================================================

set -e

MODEL_PATH=${1:-"/app/model"}
API_KEY=${2:-"vertical-sft-secret-key"}
TP_SIZE=${3:-1}

echo "========================================"
echo "  vLLM API Server 启动"
echo "========================================"
echo "  模型路径:     $MODEL_PATH"
echo "  API Key:      ${API_KEY:0:8}..."
echo "  TP Size:      $TP_SIZE"
echo "  端口:         8001"
echo "  最大长度:     4096"
echo "  显存利用率:   0.9"
echo "========================================"

python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --served-model-name vertical-sft-model \
    --tensor-parallel-size "$TP_SIZE" \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9 \
    --port 8001 \\
    --api-key "$API_KEY" \
    --trust-remote-code
