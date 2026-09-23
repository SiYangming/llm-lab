# llm-lab

Portfolio monorepo for the 八斗 AI大模型 / Agent course: small, related LLM projects in one place.

八斗 AI 大模型 / Agent 课程作品集仓库：相关小项目收进同一个 monorepo，按编号递进。

## Layout / 目录

| Path | Role |
|------|------|
| `requirements.txt` | Shared runtime deps（两个项目共用） |
| `requirements-dev.txt` | Dev deps（pytest 等） |
| `LICENSE` / `.gitignore` | Repo-wide |
| `projects/01-streaming-chat` | Streaming chat CLI |
| `projects/02-failover-chat` | Retry + circuit breaker + failover |

Later stages land as `projects/03-…`.

## Setup / 环境（一次装好）

```bash
git clone https://github.com/SiYangming/llm-lab.git
cd llm-lab
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# optional tests:
# pip install -r requirements-dev.txt
```

Each project still has its own `.env.example`（密钥与路由不同，不合并）.

## Run / 运行

```bash
# Project 01
cp projects/01-streaming-chat/.env.example projects/01-streaming-chat/.env
# edit .env, then:
PYTHONPATH=projects/01-streaming-chat python -m src.chat

# Project 02
cp projects/02-failover-chat/.env.example projects/02-failover-chat/.env
PYTHONPATH=projects/02-failover-chat python -m src.chat
```

Or `cd` into the project folder and run `python -m src.chat` with the same venv activated from the repo root.

## Tests / 测试

```bash
source venv/bin/activate
pip install -r requirements-dev.txt
PYTHONPATH=projects/02-failover-chat pytest -q projects/02-failover-chat/tests
```

## Resume / 简历写法

One repo, numbered labs, shared tooling at root, each project folder focused on the idea being demonstrated.

## License

MIT. See [LICENSE](LICENSE).
