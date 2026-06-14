FROM vllm/vllm-openai:latest

# 模型文件和启动脚本
COPY models/merged_model /app/model
COPY deploy/start_vllm.sh /app/
RUN chmod +x /app/start_vllm.sh

# 暴露 API 端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["/app/start_vllm.sh"]
