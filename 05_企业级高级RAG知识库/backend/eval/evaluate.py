"""
Evaluation script for the Enterprise RAG system.
Calculates Hit Rate@3, MRR, and generates tuning recommendations.

Usage:
    python eval/evaluate.py
    python eval/evaluate.py --tune   # Run parameter tuning grid search
"""

import json
import os
import sys
import time
import logging
from typing import List, Dict

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.core import hybrid_search, reranker

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

QA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qa_pairs.json")
REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")


def load_qa_pairs() -> List[dict]:
    """Load QA pairs from JSON file."""
    with open(QA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_retrieval(
    qa_pairs: List[dict],
    top_k: int = 3,
    bm25_weight: float = None,
    vector_weight: float = None,
) -> Dict:
    """
    Evaluate retrieval quality on the QA pairs.

    Returns dict with hit_rate@k, mrr, and per-question details.
    """
    bm25_weight = bm25_weight if bm25_weight is not None else settings.BM25_WEIGHT
    vector_weight = vector_weight if vector_weight is not None else settings.VECTOR_WEIGHT

    hits = 0
    reciprocal_ranks = []
    details = []

    for qa in qa_pairs:
        question = qa["question"]
        expected_doc = qa["expected_source_doc"]

        try:
            # Run hybrid search
            candidates = hybrid_search.hybrid_search(
                question,
                top_k=top_k * 5,  # Get more candidates for reranking
                bm25_weight=bm25_weight,
                vector_weight=vector_weight,
            )

            # Rerank
            reranked = reranker.rerank(question, candidates, top_n=top_k)
            result_docs = [r["doc_name"] for r in reranked]

        except Exception as e:
            logger.error(f"Search failed for question '{question}': {e}")
            result_docs = []

        # Check hit
        hit = expected_doc in result_docs
        if hit:
            hits += 1

        # Calculate reciprocal rank
        rr = 0.0
        for rank, doc in enumerate(result_docs):
            if doc == expected_doc:
                rr = 1.0 / (rank + 1)
                break
        reciprocal_ranks.append(rr)

        details.append({
            "question": question,
            "expected_doc": expected_doc,
            "result_docs": result_docs,
            "hit": hit,
            "reciprocal_rank": round(rr, 4),
        })

    total = len(qa_pairs)
    hit_rate = hits / total if total > 0 else 0.0
    mrr = sum(reciprocal_ranks) / total if total > 0 else 0.0

    return {
        "hit_rate_at_k": round(hit_rate, 4),
        "mrr": round(mrr, 4),
        "total_questions": total,
        "hits": hits,
        "top_k": top_k,
        "bm25_weight": bm25_weight,
        "vector_weight": vector_weight,
        "details": details,
    }


def run_parameter_tuning(qa_pairs: List[dict]) -> List[Dict]:
    """
    Grid search over BM25/Vector weights and top_k values.
    Returns sorted list of parameter combinations by performance.
    """
    weight_combos = [
        (0.2, 0.8), (0.3, 0.7), (0.4, 0.6), (0.5, 0.5), (0.6, 0.4), (0.8, 0.2),
    ]
    top_k_values = [3, 5]

    results = []

    for bm25_w, vec_w in weight_combos:
        for top_k in top_k_values:
            logger.info(f"Evaluating: BM25={bm25_w}, Vector={vec_w}, Top-K={top_k}")
            start = time.time()

            eval_result = evaluate_retrieval(
                qa_pairs, top_k=top_k, bm25_weight=bm25_w, vector_weight=vec_w,
            )
            elapsed = time.time() - start

            results.append({
                "bm25_weight": bm25_w,
                "vector_weight": vec_w,
                "top_k": top_k,
                "hit_rate@k": eval_result["hit_rate_at_k"],
                "mrr": eval_result["mrr"],
                "eval_time_s": round(elapsed, 1),
            })

            logger.info(
                f"  -> Hit Rate@{top_k}={eval_result['hit_rate_at_k']:.2%}, "
                f"MRR={eval_result['mrr']:.4f}, Time={elapsed:.1f}s"
            )

    # Sort by MRR then Hit Rate
    results.sort(key=lambda x: (x["mrr"], x["hit_rate@k"]), reverse=True)
    return results


def generate_tuning_report(tuning_results: List[Dict]) -> str:
    """Generate a markdown tuning report."""
    best = tuning_results[0]

    lines = [
        "# RAG 调参报告",
        "",
        f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 最佳参数组合",
        "",
        f"| 参数 | 值 |",
        f"|------|-----|",
        f"| BM25 权重 | {best['bm25_weight']} |",
        f"| 向量权重 | {best['vector_weight']} |",
        f"| Top-K | {best['top_k']} |",
        f"| Hit Rate@{best['top_k']} | {best['hit_rate@k']:.2%} |",
        f"| MRR | {best['mrr']:.4f} |",
        "",
        "## 全部参数组合对比",
        "",
        "| BM25权重 | 向量权重 | Top-K | Hit Rate | MRR | 评估耗时(s) |",
        "|:---------:|:--------:|:-----:|:--------:|:-----:|:-----------:|",
    ]

    for r in tuning_results:
        lines.append(
            f"| {r['bm25_weight']} | {r['vector_weight']} | {r['top_k']} | "
            f"{r['hit_rate@k']:.2%} | {r['mrr']:.4f} | {r['eval_time_s']} |"
        )

    lines.extend([
        "",
        "## 调参建议",
        "",
        f"1. **BM25/向量权重**: 推荐 `{best['bm25_weight']}:{best['vector_weight']}`，该组合在 Hit Rate 和 MRR 上表现最佳。",
        f"2. **Top-K**: 推荐 `{best['top_k']}`，平衡了准确率和召回率。",
        f"3. **Reranker 阈值**: 当前阈值 `{settings.RERANKER_THRESHOLD}`，可根据实际误召率微调。",
        "",
        "---",
        "*本报告由评估脚本自动生成*",
    ])

    return "\n".join(lines)


def generate_benchmark_report(eval_result: Dict) -> str:
    """Generate a markdown benchmark report."""
    lines = [
        "# RAG 性能基准报告",
        "",
        f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 检索效果指标",
        "",
        f"| 指标 | 值 |",
        f"|------|-----|",
        f"| Hit Rate@{eval_result['top_k']} | {eval_result['hit_rate_at_k']:.2%} |",
        f"| MRR | {eval_result['mrr']:.4f} |",
        f"| 测试题数 | {eval_result['total_questions']} |",
        f"| 命中数 | {eval_result['hits']} |",
        f"| BM25 权重 | {eval_result['bm25_weight']} |",
        f"| 向量权重 | {eval_result['vector_weight']} |",
        "",
        "## 逐题评估详情",
        "",
        "| 问题 | 期望文档 | 命中 | RR |",
        "|------|----------|:----:|:--:|",
    ]

    for d in eval_result["details"]:
        hit_mark = "✅" if d["hit"] else "❌"
        q_short = d["question"][:20] + "..." if len(d["question"]) > 20 else d["question"]
        lines.append(f"| {q_short} | {d['expected_doc']} | {hit_mark} | {d['reciprocal_rank']} |")

    lines.extend([
        "",
        "---",
        "*本报告由评估脚本自动生成*",
    ])

    return "\n".join(lines)


if __name__ == "__main__":
    os.makedirs(REPORT_DIR, exist_ok=True)

    qa_pairs = load_qa_pairs()
    logger.info(f"Loaded {len(qa_pairs)} QA pairs.")

    # Run basic evaluation with current settings
    logger.info("Running evaluation with current settings...")
    eval_result = evaluate_retrieval(qa_pairs)

    logger.info(f"\n=== Evaluation Results ===")
    logger.info(f"Hit Rate@{eval_result['top_k']}: {eval_result['hit_rate_at_k']:.2%}")
    logger.info(f"MRR: {eval_result['mrr']:.4f}")

    # Generate benchmark report
    report = generate_benchmark_report(eval_result)
    report_path = os.path.join(REPORT_DIR, "benchmark_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info(f"Benchmark report saved to {report_path}")

    # Run parameter tuning if --tune flag is passed
    if "--tune" in sys.argv:
        logger.info("\nRunning parameter tuning grid search...")
        tuning_results = run_parameter_tuning(qa_pairs)

        tuning_report = generate_tuning_report(tuning_results)
        tuning_path = os.path.join(REPORT_DIR, "tuning_report.md")
        with open(tuning_path, "w", encoding="utf-8") as f:
            f.write(tuning_report)
        logger.info(f"Tuning report saved to {tuning_path}")

        # Print best result
        best = tuning_results[0]
        logger.info(f"\n=== Best Parameters ===")
        logger.info(f"BM25:Vector = {best['bm25_weight']}:{best['vector_weight']}")
        logger.info(f"Top-K = {best['top_k']}")
        logger.info(f"Hit Rate@{best['top_k']} = {best['hit_rate@k']:.2%}")
        logger.info(f"MRR = {best['mrr']:.4f}")
