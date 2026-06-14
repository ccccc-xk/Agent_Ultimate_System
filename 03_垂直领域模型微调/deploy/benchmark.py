#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vLLM API 压测脚本
模拟并发请求，统计 QPS、延迟分布、错误率
用法: python benchmark.py --url http://localhost:8000/v1/chat/completions --api-key your-key
"""

import argparse
import asyncio
import json
import os
import random
import time

import aiohttp

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_FILE = os.path.join(BASE_DIR, "data", "test", "holdout_test.json")
REPORT_FILE = os.path.join(BASE_DIR, "docs", "benchmark_report.json")


async def send_request(session, url, api_key, payload):
    """发送单个请求，返回 (success, latency_ms, tokens, error_msg)"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    start = time.time()
    try:
        async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=60)) as resp:
            latency_ms = (time.time() - start) * 1000
            if resp.status == 200:
                data = await resp.json()
                tokens = data.get("usage", {}).get("completion_tokens", 0)
                return True, latency_ms, tokens, None
            else:
                body = await resp.text()
                return False, latency_ms, 0, f"HTTP {resp.status}: {body[:200]}"
    except asyncio.TimeoutError:
        latency_ms = (time.time() - start) * 1000
        return False, latency_ms, 0, "Timeout"
    except Exception as e:
        latency_ms = (time.time() - start) * 1000
        return False, latency_ms, 0, str(e)[:200]


async def run_benchmark(url, api_key, concurrency, total_requests, model, test_inputs):
    """执行压测"""
    semaphore = asyncio.Semaphore(concurrency)
    results = []

    async def bounded_request(session, idx, input_text):
        async with semaphore:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": input_text}],
                "max_tokens": 512,
                "temperature": 0.1,
            }
            success, latency_ms, tokens, error = await send_request(session, url, api_key, payload)
            return {
                "index": idx,
                "success": success,
                "latency_ms": round(latency_ms, 1),
                "tokens": tokens,
                "error": error,
            }

    connector = aiohttp.TCPConnector(limit=concurrency)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for i in range(total_requests):
            input_text = random.choice(test_inputs)
            tasks.append(bounded_request(session, i, input_text))

        total_start = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - total_start

    return results, total_time


def analyze_results(results, total_time, concurrency):
    """分析压测结果"""
    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]
    latencies = sorted([r["latency_ms"] for r in results])
    total_tokens = sum(r["tokens"] for r in successes)

    n = len(latencies)
    if n == 0:
        return {"error": "no results"}

    p50_idx = int(n * 0.50)
    p95_idx = int(n * 0.95)
    p99_idx = int(n * 0.99)

    qps = len(results) / total_time if total_time > 0 else 0
    token_throughput = total_tokens / total_time if total_time > 0 else 0

    report = {
        "config": {
            "concurrency": concurrency,
            "total_requests": len(results),
            "total_time_sec": round(total_time, 2),
        },
        "results": {
            "qps": round(qps, 2),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 1),
            "latency_p50_ms": round(latencies[min(p50_idx, n - 1)], 1),
            "latency_p95_ms": round(latencies[min(p95_idx, n - 1)], 1),
            "latency_p99_ms": round(latencies[min(p99_idx, n - 1)], 1),
            "min_latency_ms": round(latencies[0], 1),
            "max_latency_ms": round(latencies[-1], 1),
            "success_count": len(successes),
            "error_count": len(failures),
            "error_rate": f"{len(failures) / len(results) * 100:.2f}%",
            "total_tokens": total_tokens,
            "avg_tokens_per_request": round(total_tokens / len(successes), 1) if successes else 0,
            "token_throughput_per_sec": round(token_throughput, 1),
        },
    }

    # 错误统计
    if failures:
        error_types = {}
        for f in failures:
            err = f["error"] or "unknown"
            error_types[err] = error_types.get(err, 0) + 1
        report["error_details"] = error_types

    return report


async def main():
    parser = argparse.ArgumentParser(description="vLLM API 压测")
    parser.add_argument("--url", type=str, default="http://localhost:8000/v1/chat/completions",
                        help="API 地址")
    parser.add_argument("--api-key", type=str, default="vertical-sft-secret-key",
                        help="API Key")
    parser.add_argument("--concurrency", type=int, default=50,
                        help="并发数")
    parser.add_argument("--total", type=int, default=500,
                        help="总请求数")
    parser.add_argument("--model", type=str, default="vertical-sft-model",
                        help="模型名称")
    args = parser.parse_args()

    print("=" * 50)
    print("vLLM API 压测")
    print("=" * 50)
    print(f"  URL:         {args.url}")
    print(f"  并发数:      {args.concurrency}")
    print(f"  总请求:      {args.total}")
    print(f"  模型:        {args.model}")
    print()

    # 加载测试输入
    test_inputs = ["查一下上个月的订单总数"]  # 默认 fallback
    if os.path.exists(TEST_FILE):
        with open(TEST_FILE, "r", encoding="utf-8") as f:
            test_data = json.load(f)
        test_inputs = [s["input"] for s in test_data]
        print(f"  测试输入:    {len(test_inputs)} 条")
    print()

    print("开始压测...")
    results, total_time = await run_benchmark(
        args.url, args.api_key, args.concurrency, args.total, args.model, test_inputs
    )

    # 分析结果
    report = analyze_results(results, total_time, args.concurrency)

    r = report["results"]
    print("\n" + "=" * 50)
    print("压测结果")
    print("=" * 50)
    print(f"  QPS:              {r['qps']}")
    print(f"  平均延迟:         {r['avg_latency_ms']}ms")
    print(f"  P50 延迟:         {r['latency_p50_ms']}ms")
    print(f"  P95 延迟:         {r['latency_p95_ms']}ms")
    print(f"  P99 延迟:         {r['latency_p99_ms']}ms")
    print(f"  成功/失败:        {r['success_count']}/{r['error_count']}")
    print(f"  错误率:           {r['error_rate']}")
    print(f"  Token 吞吐量:     {r['token_throughput_per_sec']} tokens/s")
    print("=" * 50)

    if "error_details" in report:
        print("\n错误详情:")
        for err, count in report["error_details"].items():
            print(f"  [{count}次] {err}")

    # 保存报告
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n报告已保存: {REPORT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
