"""Minimal circuit breaker: closed -> open -> half-open."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class State(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    fail_threshold: int = 3
    reset_seconds: float = 30.0
    failure_count: int = 0
    opened_at: float | None = None
    state: State = field(default=State.CLOSED)

    def allow(self) -> bool:
        if self.state is State.CLOSED:
            return True
        if self.state is State.OPEN:
            assert self.opened_at is not None
            if time.monotonic() - self.opened_at >= self.reset_seconds:
                self.state = State.HALF_OPEN
                return True
            return False
        # half-open: allow one probe
        return True

    def record_success(self) -> None:
        self.failure_count = 0
        self.opened_at = None
        self.state = State.CLOSED

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.state is State.HALF_OPEN or self.failure_count >= self.fail_threshold:
            self.state = State.OPEN
            self.opened_at = time.monotonic()
