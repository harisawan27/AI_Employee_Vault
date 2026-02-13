"""
WEBXES Tech — Retry Handler & Circuit Breaker

Provides:
- @retry decorator with exponential backoff + jitter
- CircuitBreaker class (CLOSED → OPEN → HALF_OPEN)

Thread-safe. Import and use across all API callers.
"""

import functools
import logging
import random
import threading
import time
from enum import Enum

logger = logging.getLogger("retry_handler")


def retry(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0,
          exceptions: tuple = (Exception,)):
    """Decorator: exponential backoff with jitter.

    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Cap on delay between retries.
        exceptions: Tuple of exception types to catch and retry.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt == max_retries:
                        logger.error(f"{func.__name__} failed after {max_retries + 1} attempts: {e}")
                        raise
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = random.uniform(0, delay * 0.5)
                    sleep_time = delay + jitter
                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {sleep_time:.1f}s..."
                    )
                    time.sleep(sleep_time)
            raise last_exc  # unreachable but satisfies type checkers
        return wrapper
    return decorator


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Thread-safe circuit breaker for external service calls.

    Usage:
        cb = CircuitBreaker("odoo")
        with cb:
            call_external_api()
    """

    def __init__(self, name: str = "default", failure_threshold: int = 5,
                 recovery_timeout: float = 300.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if time.time() - self._last_failure_time >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    logger.info(f"CircuitBreaker[{self.name}]: OPEN → HALF_OPEN")
            return self._state

    def record_success(self):
        with self._lock:
            self._failure_count = 0
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.CLOSED
                logger.info(f"CircuitBreaker[{self.name}]: HALF_OPEN → CLOSED")

    def record_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(
                    f"CircuitBreaker[{self.name}]: CLOSED → OPEN "
                    f"(failures={self._failure_count})"
                )

    def __enter__(self):
        if self.state == CircuitState.OPEN:
            raise ConnectionError(
                f"CircuitBreaker[{self.name}] is OPEN. "
                f"Service unavailable, retry after {self.recovery_timeout}s."
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.record_success()
        else:
            self.record_failure()
        return False  # don't suppress exceptions
