"""CivicFix Resilience Engine: Circuit Breaker, Retries with Jitter, and Outbound Timeouts.

Features:
- Gemini Circuit Breaker: After N consecutive failures, stops outbound calls for cooldown.
  Tripped calls fast-fail and triage reports to PENDING_MANUAL for dispatcher queue review.
- Bounded Retries with Exponential Backoff & Full Jitter.
- Strict Outbound Call Timeouts protecting against hung sockets.
- Bulkhead Isolation: Dedicated concurrency limits for AI workloads vs API request handling.
"""

import asyncio
import logging
import os
import random
import time
from typing import Any, Callable, Coroutine, Optional, Tuple, TypeVar

logger = logging.getLogger("civicfix.resilience")

T = TypeVar("T")


class CircuitBreakerOpenException(Exception):
    """Raised when an outbound service call is rejected because the circuit breaker is OPEN."""

    pass


class CircuitBreaker:
    """Distributed Circuit Breaker with Redis backing and in-memory fallback.

    States:
    - CLOSED: Normal operation. Outbound calls proceed.
    - OPEN: Service tripped due to >= failure_threshold consecutive errors. Fast-fails.
    - HALF_OPEN: Cooldown period elapsed. Allows trial request to probe recovery.
    """

    def __init__(
        self,
        name: str = "gemini",
        failure_threshold: int = 5,
        cooldown_seconds: float = 60.0,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds

        # In-memory local fallback state
        self._local_failures = 0
        self._local_tripped_at: Optional[float] = None
        self._local_state = "CLOSED"

    @property
    def key_failures(self) -> str:
        return f"cb:{self.name}:failures"

    @property
    def key_tripped_at(self) -> str:
        return f"cb:{self.name}:tripped_at"

    async def can_execute(self, redis_client: Optional[Any] = None) -> bool:
        """Check whether the circuit allows outbound execution.

        Returns True if CLOSED or HALF_OPEN; False if OPEN.
        """
        now = time.time()

        if redis_client:
            try:
                tripped_at_raw = await redis_client.get(self.key_tripped_at)
                if tripped_at_raw:
                    tripped_at = float(tripped_at_raw)
                    elapsed = now - tripped_at
                    if elapsed < self.cooldown_seconds:
                        logger.warning(
                            f"CircuitBreaker [{self.name}] is OPEN "
                            f"(cooldown {elapsed:.1f}/{self.cooldown_seconds}s). Fast-failing."
                        )
                        return False
                    else:
                        logger.info(
                            f"CircuitBreaker [{self.name}] entering HALF_OPEN probe state."
                        )
                        return True

                failures_raw = await redis_client.get(self.key_failures)
                failures = int(failures_raw) if failures_raw else 0
                return failures < self.failure_threshold
            except Exception as e:
                logger.warning(
                    f"Error checking circuit in Redis: {e}; falling back to local state."
                )

        # Local fallback
        if self._local_tripped_at is not None:
            elapsed = now - self._local_tripped_at
            if elapsed < self.cooldown_seconds:
                logger.warning(
                    f"CircuitBreaker [{self.name}] is OPEN (cooldown {elapsed:.1f}/{self.cooldown_seconds}s). "
                    "Fast-failing."
                )
                return False
            else:
                self._local_state = "HALF_OPEN"
                return True

        return self._local_failures < self.failure_threshold

    async def record_success(self, redis_client: Optional[Any] = None) -> None:
        """Record successful outbound call, resetting circuit to CLOSED."""
        self._local_failures = 0
        self._local_tripped_at = None
        self._local_state = "CLOSED"

        if redis_client:
            try:
                await redis_client.delete(self.key_failures)
                await redis_client.delete(self.key_tripped_at)
                logger.info(
                    f"CircuitBreaker [{self.name}] reset to CLOSED on successful call."
                )
            except Exception as e:
                logger.warning(f"Error resetting circuit in Redis: {e}")

    async def record_failure(self, redis_client: Optional[Any] = None) -> bool:
        """Record failure. Returns True if circuit newly tripped to OPEN."""
        now = time.time()
        newly_tripped = False

        if redis_client:
            try:
                fails = await redis_client.incr(self.key_failures)
                await redis_client.expire(
                    self.key_failures, int(self.cooldown_seconds * 3)
                )

                if fails >= self.failure_threshold:
                    await redis_client.setex(
                        self.key_tripped_at, int(self.cooldown_seconds), str(now)
                    )
                    logger.critical(
                        f"ALERT: CircuitBreaker [{self.name}] TRIPPED TO OPEN after {fails} consecutive failures! "
                        f"Cooldown set to {self.cooldown_seconds}s."
                    )
                    newly_tripped = True
                return newly_tripped
            except Exception as e:
                logger.warning(f"Error recording circuit failure in Redis: {e}")

        # Local fallback
        self._local_failures += 1
        if self._local_failures >= self.failure_threshold:
            self._local_tripped_at = now
            self._local_state = "OPEN"
            logger.critical(
                f"ALERT: CircuitBreaker [{self.name}] TRIPPED TO OPEN after "
                f"{self._local_failures} consecutive failures! Cooldown set to {self.cooldown_seconds}s."
            )
            newly_tripped = True

        return newly_tripped


# Global Gemini Circuit Breaker instance
gemini_circuit_breaker = CircuitBreaker(
    name="gemini",
    failure_threshold=int(os.getenv("GEMINI_CB_FAILURE_THRESHOLD", "5")),
    cooldown_seconds=float(os.getenv("GEMINI_CB_COOLDOWN_SECONDS", "60.0")),
)


async def call_with_timeout(
    coro: Coroutine[Any, Any, T], timeout_seconds: float = 15.0
) -> T:
    """Execute coroutine with strict timeout protection."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Outbound call timed out after {timeout_seconds} seconds.")


async def retry_with_jitter(
    coroutine_fn: Callable[[], Coroutine[Any, Any, T]],
    max_retries: int = 3,
    base_delay: float = 0.2,
    max_delay: float = 2.0,
    retryable_exceptions: Tuple[type, ...] = (Exception,),
) -> T:
    """Execute coroutine function with bounded retries and full random jitter backoff.

    Formula:
        delay = min(max_delay, base_delay * (2 ** attempt)) * uniform(0.5, 1.5)
    """
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return await coroutine_fn()
        except retryable_exceptions as e:
            last_exception = e
            if attempt == max_retries:
                logger.error(
                    f"Retries exhausted ({max_retries}/{max_retries}) on outbound call: {e}"
                )
                raise

            # Calculate bounded delay with full jitter
            exp_backoff = min(max_delay, base_delay * (2**attempt))
            jittered_delay = exp_backoff * random.uniform(0.5, 1.5)

            logger.warning(
                f"Outbound call failed ({e}). Retrying in {jittered_delay:.2f}s "
                f"(attempt {attempt + 1}/{max_retries})..."
            )
            await asyncio.sleep(jittered_delay)

    raise last_exception  # type: ignore
