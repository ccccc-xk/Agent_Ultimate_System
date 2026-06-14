# 训练报告

> 本文件为模板，训练完成后补充实际数据。

---

## 数据集统计

| 指标 | 数值 |
|---|---|
| 原始数据 | 180 条（3 场景 × 60 条） |
| 精确去重后 | 177 条 |
| 模糊去重后 | 168 条 |
| 格式校验后 | 161 条 |
| 最终训练集 | 141 条 |
| 验证集（Holdout） | 20 条 |

### 场景分布

| 场景 | 训练集 | 测试集 |
|---|---|---|
| 投诉分类归因 | 44 | 7 |
| 口语化工单提取 | 60 | 7 |
| 自然语言转SQL | 44 | 6 |

---

## 训练超参数

| 参数 | 值 |
|---|---|
| 基座模型 | Qwen/Qwen2.5-7B-Instruct |
| 微调方式 | LoRA (rank=16, alpha=32) |
| 目标模块 | q_proj, v_proj |
| 学习率 | 2e-4 |
| 训练轮数 | 3 |
| Batch Size | 4 × 4 (gradient_accumulation) = 16 |
| 精度 | bf16 |
| 调度器 | cosine |
| Warmup | 0.1 |
| Cutoff Length | 1024 |

---

## 训练 Loss 曲线

> 训练完成后，从 `logs/loss_history.jsonl` 读取数据。
> 可用以下脚本生成 loss 曲线图：

```python
import json
import matplotlib.pyplot as plt

data = []
with open("logs/loss_history.jsonl") as f:
    for line in f:
        data.append(json.loads(line))

steps = [d["step"] for d in data]
losses = [d["loss"] for d in data]

plt.figure(figsize=(10, 6))
plt.plot(steps, losses)
plt.xlabel("Step")
plt.ylabel("Loss")
plt.title("Training Loss Curve")
plt.grid(True)
plt.savefig("docs/loss_curve.png", dpi=150)
plt.show()
```

---

## 验证结果

> 训练完成后，运行 `python scripts/validate_model.py` 并将结果填入此处。

| 指标 | 结果 |
|---|---|
| 合规率 | 待填 |
| 通过数 | 待填 |
| 失败数 | 待填 |

---

## 结论与建议

> 根据验证结果填写。
