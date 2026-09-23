import time

from src.circuit_breaker import CircuitBreaker, State


def test_opens_after_threshold():
    cb = CircuitBreaker(fail_threshold=2, reset_seconds=0.05)
    assert cb.allow()
    cb.record_failure()
    assert cb.state is State.CLOSED
    cb.record_failure()
    assert cb.state is State.OPEN
    assert not cb.allow()
    time.sleep(0.06)
    assert cb.allow()  # half-open
    assert cb.state is State.HALF_OPEN
    cb.record_success()
    assert cb.state is State.CLOSED
