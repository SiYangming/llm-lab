> Part of the [llm-lab](https://github.com/SiYangming/llm-lab) monorepo (八斗 AI course).
>
> 本目录属于 monorepo [llm-lab](https://github.com/SiYangming/llm-lab)。共享依赖在仓库根目录的 `requirements.txt` / `LICENSE` / `.gitignore`。

# llm-failover-chat

Portfolio CLI: streaming chat with **retry**, **circuit breaker**, and **primary → fallback** provider routing. Course project: 八斗 AI Project 2.

面向简历的可靠性小项目：流式对话 + 重试退避 + 熔断 + 主备切换。课程项目：八斗 AI Project 2。

## Why / 为什么做

Project 1 proves you can call an LLM. Project 2 proves the call still works when the primary provider times out, rate-limits, or returns 5xx.

项目1证明你会调模型；项目2证明主源挂了还能稳住服务。

## Behavior / 行为

1. Classify errors: transient (timeout / 429 / 5xx) vs fatal (401 / 400)
2. Retry transient errors with exponential backoff + jitter
3. Trip a per-provider circuit breaker after repeated failures
4. Route to the next provider in order while the primary circuit is open
5. Stream tokens the same way as Project 1; print which provider answered

## Setup / 本地环境

```bash
git clone https://github.com/SiYangming/llm-lab.git
cd llm-lab/projects/02-failover-chat
python3 -m venv venv
source venv/bin/activate
pip install -r ../../requirements.txt  # from this folder; or install once at repo root
cp .env.example .env
```

Fill at least `PRIMARY_API_KEY`. For a real failover demo, set `FALLBACK_API_KEY` (can be another key/base_url/model).

## Run / 运行

```bash
source venv/bin/activate
python -m src.chat
```

Commands: `/exit`, `/clear`, `/status` (show circuit state).

## Demo ideas / 演示思路

- Happy path: only primary configured → same as Project 1
- Failover: point `PRIMARY_BASE_URL` at a dead host, keep fallback valid → reply tagged `[fallback]`
- Circuit: hammer a bad primary until `/status` shows `open`, then watch it skip primary

## Tests / 测试

```bash
pip install pytest
pytest -q
```

## Resume bullet / 简历要点

- Implemented LLM client failover with error classification, bounded retries, and a closed/open/half-open circuit breaker.
- Kept a single streaming chat UX while routing across primary/fallback OpenAI-compatible providers.

## License

MIT. See [LICENSE](LICENSE).

## Demo（已验证）

```bash
# 在仓库根目录
source venv/bin/activate
PYTHONPATH=projects/02-failover-chat python -m pytest -q projects/02-failover-chat/tests
# ... 3 passed in 0.61s

PYTHONPATH=projects/02-failover-chat python -m src.chat
```

```text
LLM failover chat | providers=[primary:deepseek-chat, fallback:deepseek-chat]
Commands: /exit /clear /status

You: hi
Assistant: ...
  [primary]
```

主源失败时末尾变为 `[fallback]`。截图：

![primary](docs/screenshots/chat-primary.png)

![fallback](docs/screenshots/chat-fallback.png)

