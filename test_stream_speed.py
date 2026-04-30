#!/usr/bin/env python3
"""客户端流式请求速度测试"""

import time
import statistics
import yaml
from openai import OpenAI


def single_test(client, model, prompt, max_tokens=500):
    """单次流式请求测试，返回 (token_count, duration, ttft, per_token_times)"""
    start_time = time.perf_counter()
    token_count = 0
    first_token_time = None
    prev_token_time = None
    per_token_times = []

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        temperature=0.7,
        top_p=0.8,
        max_tokens=max_tokens,
    )

    for chunk in response:
        delta = chunk.choices[0].delta
        has_content = delta.content or getattr(delta, "reasoning_content", None)
        if has_content:
            now = time.perf_counter()
            token_count += 1

            if first_token_time is None:
                first_token_time = now

            if prev_token_time is not None:
                per_token_times.append(now - prev_token_time)

            prev_token_time = now

    duration = time.perf_counter() - start_time
    ttft = (first_token_time - start_time) if first_token_time else None

    return token_count, duration, ttft, per_token_times


def test_speed(api_key, base_url, model, prompt, max_tokens=500, num_tests=5):
    """多次测试取平均值"""
    client = OpenAI(api_key=api_key, base_url=base_url)

    speeds = []
    ttfss = []
    tpots = []

    for i in range(num_tests):
        token_count, duration, ttft, per_token_times = single_test(
            client, model, prompt, max_tokens
        )
        speed = token_count / duration if duration > 0 else 0
        tpot = (
            statistics.mean(per_token_times) * 1000 if per_token_times else None
        )

        speeds.append(speed)
        ttfss.append(ttft * 1000 if ttft else None)
        tpots.append(tpot)

        print(
            f"第 {i + 1} 次: "
            f"{token_count} tokens, "
            f"{speed:.2f} tok/s, "
            f"TTFT={ttft * 1000 if ttft else 0:.0f}ms, "
            f"TPOT={tpot if tpot else 0:.2f}ms"
        )

    # 汇总
    print("\n" + "=" * 50)
    print("汇总结果")
    print("=" * 50)
    print(f"平均速度: {statistics.mean(speeds):.2f} tokens/s")
    print(f"速度标准差: {statistics.stdev(speeds):.2f}" if len(speeds) > 1 else "")

    valid_ttfss = [t for t in ttfss if t is not None]
    if valid_ttfss:
        print(f"平均 TTFT: {statistics.mean(valid_ttfss):.0f}ms")

    valid_tpots = [t for t in tpots if t is not None]
    if valid_tpots:
        print(f"平均 TPOT: {statistics.mean(valid_tpots):.2f}ms")
    print("=" * 50)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="流式请求速度测试")
    parser.add_argument(
        "--model", required=True, help="模型名称，例如 deepseek-v4-flash"
    )
    parser.add_argument(
        "--prompt",
        default="请生成一篇500字的短文，介绍深度学习的原理。",
        help="测试提示词",
    )
    parser.add_argument(
        "--max-tokens", type=int, default=500, help="最大生成 token 数"
    )
    parser.add_argument(
        "--num-tests", type=int, default=5, help="测试次数"
    )
    args = parser.parse_args()

    with open("config.yml") as f:
        config = yaml.safe_load(f)

    provider_cfg = None
    for provider, cfg in config.items():
        if args.model in cfg["models"]:
            provider_cfg = cfg
            break

    if provider_cfg is None:
        print(f"错误: 未找到模型 '{args.model}' 的配置")
        exit(1)

    test_speed(
        api_key=provider_cfg["api_key"],
        base_url=provider_cfg["base_url"],
        model=args.model,
        prompt=args.prompt,
        max_tokens=args.max_tokens,
        num_tests=args.num_tests,
    )
