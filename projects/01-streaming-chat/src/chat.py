#!/usr/bin/env python3
"""Multi-turn streaming chat against DeepSeek's OpenAI-compatible API."""

import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"


def main() -> None:
    load_dotenv()

    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        print(
            "Missing DEEPSEEK_API_KEY. Copy .env.example to .env and set your key.",
            file=sys.stderr,
        )
        sys.exit(1)

    base_url = os.getenv("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL
    model = os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL

    client = OpenAI(api_key=api_key, base_url=base_url)
    messages: list[dict[str, str]] = []

    print(f"DeepSeek streaming chat  |  model={model}")
    print("Commands: /exit  /clear")
    print()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue
        if user_input.lower() in {"/exit", "/quit"}:
            break
        if user_input.lower() == "/clear":
            messages.clear()
            print("Conversation cleared.\n")
            continue

        messages.append({"role": "user", "content": user_input})
        print("Assistant: ", end="", flush=True)
        parts: list[str] = []

        try:
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
            )
            for chunk in stream:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content or ""
                if not content:
                    continue
                print(content, end="", flush=True)
                parts.append(content)
        except KeyboardInterrupt:
            print("\n")
            if parts:
                messages.append({"role": "assistant", "content": "".join(parts)})
            else:
                messages.pop()
            continue
        except Exception as exc:
            print(file=sys.stderr)
            print(f"Error: {exc}", file=sys.stderr)
            if parts:
                messages.append({"role": "assistant", "content": "".join(parts)})
            else:
                messages.pop()
            print()
            continue

        print("\n")
        messages.append({"role": "assistant", "content": "".join(parts)})


if __name__ == "__main__":
    main()
