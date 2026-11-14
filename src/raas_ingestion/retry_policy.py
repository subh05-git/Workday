from dataclasses import dataclass
from typing import Callable, Optional, TypeVar
import random
import time

T = TypeVar("T")


class RetryableHTTPError(Exception):
    def __init__(self, status_code: int, message: str = "", retry_after: Optional[float] = None) -> None:
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code
        self.retry_after = retry_after


class NonRetryableHTTPError(Exception):
    def __init__(self, status_code: int, message: str = "") -> None:
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code


class RetryExhaustedError(Exception):
    pass


@dataclass(frozen=True)
class RetryConfig:
    max_attempts: int = 4
    base_delay: float = 0.5
    max_delay: float = 16.0
    jitter_ratio: float = 0.2
    retryable_status_codes: tuple[int, ...] = (429, 500, 502, 503, 504)


def compute_backoff_delay(
    attempt: int,
    config: RetryConfig,
    retry_after: Optional[float] = None,
    rng: Optional[random.Random] = None,
) -> float:
    if retry_after is not None and retry_after >= 0:
        return min(retry_after, config.max_delay)
    exp = min(config.base_delay * (2 ** (attempt - 1)), config.max_delay)
    if config.jitter_ratio <= 0:
        return exp
    rand = rng.uniform(-config.jitter_ratio, config.jitter_ratio) if rng else random.uniform(-config.jitter_ratio, config.jitter_ratio)
    return max(0.0, exp * (1.0 + rand))


def execute_with_retry(
    fn: Callable[[], T],
    config: Optional[RetryConfig] = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    rng: Optional[random.Random] = None,
) -> T:
    cfg = config or RetryConfig()
    last_exc: Optional[Exception] = None
    for attempt in range(1, cfg.max_attempts + 1):
        try:
            return fn()
        except RetryableHTTPError as exc:
            last_exc = exc
            if exc.status_code not in cfg.retryable_status_codes or attempt == cfg.max_attempts:
                break
            delay = compute_backoff_delay(attempt, cfg, retry_after=exc.retry_after, rng=rng)
            sleep_fn(delay)
    raise RetryExhaustedError(f"Failed after {cfg.max_attempts} attempts: {last_exc}") from last_exc
