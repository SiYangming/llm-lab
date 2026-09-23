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

## Failover 截图怎么拍 / How to capture failover

1. `.env` 里 primary、fallback 都填有效密钥；跑通后对话末尾应是 `[primary]`（已有 `docs/screenshots/chat-primary.png`）。
2. 把 primary 的 Base URL 改成无效地址（例如 `https://127.0.0.1:9`），保存后重启：
   `PYTHONPATH=projects/02-failover-chat python -m src.chat`
3. 再聊一句，末尾应为 `[fallback]`；可选输入 `/status` 看熔断状态。截一张含 `[fallback]` 的终端图（已有 `docs/screenshots/chat-fallback.png`）。
4. 简历/作品集里两张图并排：左 primary、右 fallback，说明「主源挂了仍可对话」。

## Tests / 测试

在仓库根目录：

```bash
source venv/bin/activate
pip install -r ../../requirements-dev.txt   # 或根目录 requirements-dev.txt
PYTHONPATH=projects/02-failover-chat python -m pytest -q projects/02-failover-chat/tests
# 期望：3 passed
```

## Resume bullet / 简历要点（CN / EN）

中文：

- 实现 LLM 流式对话的主备故障转移：瞬时/致命错误分类、指数退避 + jitter 重试、closed→open→half-open 熔断；主源故障时自动切 fallback，CLI 体验不变。
- 单测覆盖熔断与错误分类；真机截图证明 `[primary]` / `[fallback]` 路由（见 `docs/screenshots/`）。

English:

- Implemented streaming LLM client failover with error classification, bounded retries (backoff + jitter), and a closed/open/half-open circuit breaker across OpenAI-compatible providers.
- Unit-tested breaker/error paths; live demos tagged `[primary]` / `[fallback]` (screenshots in `docs/screenshots/`).

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

