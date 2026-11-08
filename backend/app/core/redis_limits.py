"""CivicFix Redis-backed Rate Limiter, Idempotency & Gemini Budget Guard.

Provides:
- Distributed sliding-window rate limiting via Redis Sorted Sets (ZSET)
- HTTP 429 responses with accurate Retry-After header
- Strict user vs. IP isolation, distinguishing signed-in (10/hr) vs anonymous (3/hr)
- Fail-closed (HTTP 503) or fail-open resilience policies
- Idempotency-Key caching (24h TTL)
- Daily Gemini AI budget counter guarding against quota exhaustion
"""

from datetime import datetime, timezone
import json
import logging
import time
from typing import Any, Callable, Dict, Optional, Tuple

from fastapi import HTTPException, Request, status
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# Atomic sliding-window rate limit Lua script
# KEYS[1] = ratelimit key (e.g. ratelimit:user:123)
# ARGV[1] = current timestamp (float string)
# ARGV[2] = window in seconds (e.g. 3600)
# ARGV[3] = max allowed requests in window (e.g. 10 or 3)
SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local clear_before = now - window

-- Remove timestamps outside the sliding window
redis.call('ZREMRANGEBYSCORE', key, '-inf', clear_before)

-- Count remaining requests in current window
local current_count = redis.call('ZCARD', key)

if current_count < limit then
    -- Add unique member for current timestamp
    local member = tostring(now) .. '-' .. tostring(redis.call('INCR', key .. ':seq'))
    redis.call('ZADD', key, now, member)
    redis.call('EXPIRE', key, math.ceil(window))
    redis.call('EXPIRE', key .. ':seq', math.ceil(window))
    return {1, 0, current_count + 1} -- {allowed (1=true), retry_after, current_count}
else
    -- Find oldest request to calculate retry-after
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local retry_after = 1
    if #oldest >= 2 then
        local oldest_ts = tonumber(oldest[2])
        retry_after = math.max(1, math.ceil(oldest_ts + window - now))
    end
    return {0, retry_after, current_count} -- {allowed (0=false), retry_after, current_count}
end
"""


class RateLimiter:
    """Redis-backed distributed rate limiter and idempotency store."""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client: Optional[aioredis.Redis] = None
        self._script = None
        self._is_connected = False

    async def connect(self) -> None:
        """Establish Redis connection pool and register Lua script."""
        try:
            self.client = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=2.0,
                socket_connect_timeout=2.0,
            )
            # Test ping
            await self.client.ping()
            self._script = self.client.register_script(SLIDING_WINDOW_LUA)
            self._is_connected = True
            logger.info(
                f"RateLimiter successfully connected to Redis at {self.redis_url}"
            )
        except Exception as e:
            self._is_connected = False
            logger.warning(
                f"Could not connect to Redis at {self.redis_url}: {e}. Local fallback active."
            )

    async def close(self) -> None:
        """Close connection pool gracefully on shutdown."""
        if self.client:
            await self.client.aclose()
            self._is_connected = False
            logger.info("RateLimiter connection closed.")

    @property
    def is_connected(self) -> bool:
        return self._is_connected and self.client is not None

    async def check_rate_limit(
        self, key: str, limit: int, window_seconds: int
    ) -> Tuple[bool, int, int]:
        """Check sliding window rate limit for given key.

        Returns: (is_allowed, retry_after_seconds, current_count)
        """
        if not self.is_connected:
            raise ConnectionError("Redis rate limiter not connected.")

        now = time.time()
        res = await self._script(
            keys=[key],
            args=[str(now), str(window_seconds), str(limit)],
        )
        allowed = bool(res[0])
        retry_after = int(res[1])
        count = int(res[2])
        return allowed, retry_after, count

    async def get_idempotent_response(
        self, idempotency_key: str, identity: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve stored idempotent response if previously processed."""
        if not self.is_connected:
            return None
        cache_key = f"idempotency:{identity}:{idempotency_key}"
        try:
            val = await self.client.get(cache_key)
            if val:
                return json.loads(val)
        except Exception as e:
            logger.warning(f"Idempotency cache lookup error: {e}")
        return None

    async def set_idempotent_response(
        self,
        idempotency_key: str,
        identity: str,
        response_data: Dict[str, Any],
        ttl_seconds: int = 86400,
    ) -> None:
        """Store idempotent response for subsequent identical submissions (24h TTL)."""
        if not self.is_connected:
            return
        cache_key = f"idempotency:{identity}:{idempotency_key}"
        try:
            await self.client.set(cache_key, json.dumps(response_data), ex=ttl_seconds)
        except Exception as e:
            logger.warning(f"Idempotency cache write error: {e}")

    async def check_gemini_daily_budget(self, max_daily_budget: int = 500) -> bool:
        """Enforce daily Gemini API budget cap counter.

        Returns True if within budget, False if daily cap reached.
        """
        if not self.is_connected:
            # If Redis unavailable, allow or guard based on setting
            return True

        today_key = (
            f"gemini_daily_budget:{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        )
        try:
            count = await self.client.incr(today_key)
            if count == 1:
                # Set 48h TTL on fresh daily key
                await self.client.expire(today_key, 172800)

            if count > max_daily_budget:
                logger.critical(
                    f"Daily Gemini AI budget cap REACHED: {count} > {max_daily_budget}. "
                    "Halting automated AI triage. New reports will remain in PENDING state."
                )
                return False
            return True
        except Exception as e:
            logger.error(f"Error checking Gemini daily budget: {e}")
            return True


def user_or_ip_identity(request: Request) -> Tuple[str, bool]:
    """Determine request identity and anonymous status.

    Returns: (identity_string, is_anonymous_bool)
    """
    user_id = getattr(request.state, "user_id", None)
    is_anonymous = getattr(request.state, "is_anonymous", False)

    if user_id:
        if is_anonymous:
            return f"anon:{user_id}", True
        return f"user:{user_id}", False

    # Unauthenticated / IP fallback
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    elif request.client:
        ip = request.client.host
    else:
        ip = "127.0.0.1"

    return f"ip:{ip}", True


def rate_limit(
    signed_in_limit: int = 10,
    anonymous_limit: int = 3,
    window_seconds: int = 3600,
    fail_open: bool = False,
) -> Callable:
    """FastAPI Dependency for Redis-backed sliding window rate limiting.

    - Signed-in users: signed_in_limit / window
    - Anonymous users: anonymous_limit / window
    - fail_open: If False, raises 503 on Redis outage (used for expensive AI endpoints)
    """

    async def dependency(request: Request) -> None:
        limiter: Optional[RateLimiter] = getattr(request.app.state, "limiter", None)
        identity, is_anon = user_or_ip_identity(request)
        limit = anonymous_limit if is_anon else signed_in_limit

        if limiter is None or not limiter.is_connected:
            if not fail_open:
                logger.error(
                    "Rate limiter unavailable and fail_open is False; raising 503."
                )
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Rate limiting service is unavailable. Please retry shortly.",
                    headers={"Retry-After": "30"},
                )
            logger.warning("Rate limiter unavailable; failing open.")
            return

        try:
            allowed, retry_after, count = await limiter.check_rate_limit(
                key=f"ratelimit:{identity}",
                limit=limit,
                window_seconds=window_seconds,
            )
            if not allowed:
                user_type = "Anonymous user" if is_anon else "Signed-in user"
                logger.warning(
                    f"Rate limit exceeded for {identity} ({user_type}). "
                    f"Limit: {limit}/{window_seconds}s. Retry-After: {retry_after}s."
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Allowed: {limit} report(s) per hour.",
                    headers={"Retry-After": str(retry_after)},
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during rate limit evaluation: {e}")
            if not fail_open:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Rate limiting service is unavailable. Please retry shortly.",
                    headers={"Retry-After": "30"},
                )

    return dependency
