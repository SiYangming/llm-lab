"""Ordered provider routing with retry + circuit breaker."""

from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass
from typing import Iterator

from openai import OpenAI

from .circuit_breaker import CircuitBreaker
from .errors import FatalProviderError, TransientProviderError, classify_exception


@dataclass
class Provider:
    name: str
    client: OpenAI
    model: str
    breaker: CircuitBreaker


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    return int(raw) if raw else default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    return float(raw) if raw else default


def build_providers() -> list[Provider]:
    providers: list[Provider] = []
    primary_key = os.getenv("PRIMARY_API_KEY", "").strip()
    if primary_key:
        providers.append(
            Provider(
                name="primary",
                client=OpenAI(
                    api_key=primary_key,
                    base_url=os.getenv("PRIMARY_BASE_URL", "https://api.deepseek.com").strip(),
                ),
                model=os.getenv("PRIMARY_MODEL", "deepseek-chat").strip() or "deepseek-chat",
                breaker=CircuitBreaker(
                    fail_threshold=_env_int("CIRCUIT_FAIL_THRESHOLD", 3),
                    reset_seconds=_env_float("CIRCUIT_RESET_SECONDS", 30.0),
                ),
            )
        )
    fallback_key = os.getenv("FALLBACK_API_KEY", "").strip()
    if fallback_key:
        providers.append(
            Provider(
                name="fallback",
                client=OpenAI(
                    api_key=fallback_key,
                    base_url=os.getenv("FALLBACK_BASE_URL", "https://api.deepseek.com").strip(),
                ),
                model=os.getenv("FALLBACK_MODEL", "deepseek-chat").strip() or "deepseek-chat",
                breaker=CircuitBreaker(
                    fail_threshold=_env_int("CIRCUIT_FAIL_THRESHOLD", 3),
                    reset_seconds=_env_float("CIRCUIT_RESET_SECONDS", 30.0),
                ),
            )
        )
    if not providers:
        raise SystemExit(
            "No providers configured. Set PRIMARY_API_KEY (and optionally FALLBACK_API_KEY) in .env"
        )
    return providers


def _backoff_sleep(attempt: int) -> None:
    # 1s, 2s, 4s ... plus jitter
    base = min(2**attempt, 8)
    time.sleep(base + random.uniform(0, 0.3))


def stream_chat(providers: list[Provider], messages: list[dict[str, str]]) -> Iterator[tuple[str, str]]:
    """Yield (provider_name, delta_text). Tries providers in order with retry/breaker."""
    max_retries = _env_int("MAX_RETRIES", 2)
    last_error: BaseException | None = None

    for provider in providers:
        if not provider.breaker.allow():
            continue

        for attempt in range(max_retries + 1):
            try:
                stream = provider.client.chat.completions.create(
                    model=provider.model,
                    messages=messages,
                    stream=True,
                )
                for chunk in stream:
                    if not chunk.choices:
                        continue
                    content = chunk.choices[0].delta.content or ""
                    if content:
                        yield provider.name, content
                provider.breaker.record_success()
                return
            except Exception as exc:  # noqa: BLE001 - classified below
                kind = classify_exception(exc)
                last_error = exc
                if kind is FatalProviderError:
                    raise FatalProviderError(f"{provider.name}: {exc}") from exc
                provider.breaker.record_failure()
                if attempt < max_retries and provider.breaker.allow():
                    _backoff_sleep(attempt)
                    continue
                break  # move to next provider

    if last_error is not None:
        raise TransientProviderError(f"all providers failed: {last_error}") from last_error
    raise TransientProviderError("all providers unavailable (circuits open)")
