# llm-lab

Portfolio monorepo for the 八斗 AI大模型 / Agent course: small, related LLM projects in one place.

八斗 AI 大模型 / Agent 课程作品集仓库：相关小项目收进同一个 monorepo，按编号递进。

## Projects / 项目

| # | Folder | What it shows |
|---|--------|----------------|
| 01 | [projects/01-streaming-chat](projects/01-streaming-chat) | DeepSeek (OpenAI-compatible) streaming chat CLI |
| 02 | [projects/02-failover-chat](projects/02-failover-chat) | Retry + circuit breaker + primary→fallback routing |

Later stages (classification, NER, RAG, agents, …) land here as `03-…`, `04-…`.

## Quick start / 快速开始

Each project has its own `requirements.txt` and `.env.example`. Example for project 01:

```bash
git clone https://github.com/SiYangming/llm-lab.git
cd llm-lab/projects/01-streaming-chat
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill API key
python -m src.chat
```

## Resume / 简历写法

One repo, numbered labs, each with a focused README and runnable CLI. Prefer linking this monorepo rather than the old single-project URLs.

## License

MIT. See [LICENSE](LICENSE).
