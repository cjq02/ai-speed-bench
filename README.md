# AI Speed Bench

一个用于测试 OpenAI 兼容接口流式输出速度的轻量脚本。

当前仓库主要提供 `test_stream_speed.py`，用于多次发送同一条提示词，请求模型流式生成内容，并统计以下指标：

- `tokens/s`：整体输出吞吐速度
- `TTFT`：Time To First Token，首 token 返回耗时
- `TPOT`：Time Per Output Token，相邻输出 token 的平均间隔

适合用于：

- 对比不同模型的流式输出速度
- 对比不同网关、代理或推理服务的响应表现
- 快速观察首包延迟和持续输出稳定性

## 项目结构

```text
.
├── config.yml              # 供应商 API 配置（api_key / base_url / models）
├── test_stream_speed.py    # 主测试脚本
├── requirements.txt        # Python 依赖
└── .gitignore
```

## 运行环境

- Python 3.10+
- 支持 OpenAI SDK 的兼容接口

## 安装依赖

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 配置文件 (`config.yml`)

在 `config.yml` 中配置要测试的供应商和模型，格式如下：

```yaml
供应商名称:
  api_key: your_api_key
  base_url: https://your-openai-compatible-endpoint/v1
  models:
    - model-name-1
    - model-name-2
```

`test_stream_speed.py` 通过 `--model` 参数匹配 `config.yml` 中各供应商 `models` 列表，自动确定使用的 `api_key` 和 `base_url`。

请勿将包含真实 API Key 的 `config.yml` 提交到版本控制中。建议将 `config.yml` 加入 `.gitignore` 或使用环境变量管理密钥。

## 使用方法

`--model` 是必选参数，模型名称需在 `config.yml` 中注册：

```bash
python test_stream_speed.py --model deepseek-v4-flash
```

自定义提示词：

```bash
python test_stream_speed.py --model deepseek-v4-flash --prompt "请用 500 字解释 Transformer 的核心思想"
```

自定义最大输出 token 数：

```bash
python test_stream_speed.py --model deepseek-v4-flash --max-tokens 800
```

自定义测试次数：

```bash
python test_stream_speed.py --model deepseek-v4-flash --num-tests 3
```

组合使用：

```bash
python test_stream_speed.py \
  --model deepseek-v4-flash \
  --prompt "请生成一篇介绍深度学习原理的短文" \
  --max-tokens 500 \
  --num-tests 5
```

## 输出示例

```text
第 1 次: 412 tokens, 28.34 tok/s, TTFT=521ms, TPOT=35.41ms
第 2 次: 405 tokens, 27.92 tok/s, TTFT=498ms, TPOT=35.87ms

==================================================
汇总结果
==================================================
平均速度: 28.13 tokens/s
速度标准差: 0.30
平均 TTFT: 510ms
平均 TPOT: 35.64ms
==================================================
```

## 指标说明

### 1. `tokens/s`

整体吞吐速度，计算方式为：

```text
token_count / total_duration
```

值越大，表示流式输出越快。

### 2. `TTFT`

首 token 返回时间，表示从请求发出到收到第一个输出片段的耗时。

这个指标通常反映：

- 网络往返延迟
- 网关转发耗时
- 模型首包生成时间

值越小越好。

### 3. `TPOT`

每个输出 token 的平均时间间隔，单位是毫秒。

这个指标更接近模型持续生成阶段的稳定速度，能帮助区分：

- 首包慢，但后续输出快
- 首包快，但持续输出一般

值越小越好。

## 实现说明

脚本当前采用以下方式统计结果：

- 开启 `stream=True` 进行流式请求
- 每收到一个包含内容的流式片段，就记一次输出事件
- 用输出事件数量近似 `token_count`
- 对多次测试结果取平均值，并输出标准差

需要注意：这里的 `token_count` 实际上是"收到的有效流式片段数量"，不一定严格等于模型 tokenizer 意义上的真实 token 数。因此这个脚本更适合做相对对比测试，而不是精确计费统计。

## 依赖

`requirements.txt` 当前包含：

- `openai`
- `pyyaml`

## 注意事项

- 不同服务端对流式 chunk 的切分方式不同，因此不同平台之间的 `token_count` 和 `TPOT` 可能存在口径差异。
- 如果服务端会输出 reasoning 字段，脚本也会将其视为有效输出事件。
- 测试结果会受到网络、并发负载、服务端限流和模型缓存策略影响，建议在相同条件下多次对比。

## 后续可扩展方向

- 输出 JSON/CSV 报告
- 支持并发压测
- 区分 `content token` 与 `reasoning token`
- 记录完整响应时间分布（P50/P95/P99）
- 支持多个模型批量对比
