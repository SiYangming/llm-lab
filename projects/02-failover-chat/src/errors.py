"""Classify provider errors into retryable vs fatal."""

from __future__ import annotations

from openai import APIConnectionError, APIStatusError, APITimeoutError, RateLimitError


class FatalProviderError(Exception):
    """Do not retry or fail over for the same credentials/config."""


class TransientProviderError(Exception):
    """Safe to retry or fail over."""


def classify_exception(exc: BaseException) -> type[Exception]:
    """Return TransientProviderError or FatalProviderError class for *exc*."""
    if isinstance(exc, (APITimeoutError, APIConnectionError, RateLimitError)):
        return TransientProviderError
    if isinstance(exc, APIStatusError):
        status = getattr(exc, "status_code", None) or 0
        if status in {408, 409, 425, 429} or status >= 500:
            return TransientProviderError
        if status in {400, 401, 403, 404, 422}:
            return FatalProviderError
        return TransientProviderError
    return TransientProviderError
