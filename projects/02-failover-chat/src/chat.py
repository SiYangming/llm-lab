#!/usr/bin/env python3
"""Streaming chat CLI with primary -> fallback failover."""

from __future__ import annotations

import sys

from dotenv import load_dotenv

from .errors import FatalProviderError, TransientProviderError
from .failover import build_providers, stream_chat


def main() -> None:
    load_dotenv()
    providers = build_providers()
    names = ", ".join(f"{p.name}:{p.model}" for p in providers)
    print(f"LLM failover chat  |  providers=[{names}]")
    print("Commands: /exit  /clear  /status")
    print()

    messages: list[dict[str, str]] = []

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
        if user_input.lower() == "/status":
            for p in providers:
                print(f"  {p.name}: circuit={p.breaker.state.value} fails={p.breaker.failure_count}")
            print()
            continue

        messages.append({"role": "user", "content": user_input})
        print("Assistant: ", end="", flush=True)
        parts: list[str] = []
        active: str | None = None

        try:
            for name, delta in stream_chat(providers, messages):
                if active is None:
                    active = name
                elif name != active:
                    # should not happen mid-stream in this design
                    active = name
                print(delta, end="", flush=True)
                parts.append(delta)
        except (FatalProviderError, TransientProviderError) as exc:
            print(file=sys.stderr)
            print(f"Error: {exc}", file=sys.stderr)
            messages.pop()
            print()
            continue
        except KeyboardInterrupt:
            print("\n")
            if parts:
                messages.append({"role": "assistant", "content": "".join(parts)})
            else:
                messages.pop()
            continue

        print(f"\n  [{active}]\n")
        messages.append({"role": "assistant", "content": "".join(parts)})


if __name__ == "__main__":
    main()
