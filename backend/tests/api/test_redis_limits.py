"""Pytest suite for CivicFix Phase 1: Redis Rate Limiting & Scale Guard.

Verifies:
1. HTTP 429 and Retry-After header on exceeding rate limit
2. Per-user isolation (one user reaching limit does not block others)
3. Anonymous users stricter than signed-in users (3/hr vs 10/hr)
4. Idempotent retry with Idempotency-Key returns the same report without double-counting
5. Redis outage -> expensive route (POST /reports) fails closed with HTTP 503
6. Daily Gemini budget guard caps automated AI jobs when budget threshold reached
"""

import asyncio
from datetime import datetime, timezone
import json
import time
from typing import Any, Dict, List, Optional, Tuple
import jwt
import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from app.core.config import settings
from app.core.redis_limits import RateLimiter, rate_limit, user_or_ip_identity
import reports_api
from reports_api import _in_memory_reports, _in_memory_issues, _rate_limits


class MockRateLimiter:
    """High-fidelity in-memory RateLimiter for deterministic async tests."""

    def __init__(self, connected: bool = True):
        self._connected = connected
        self.windows: Dict[str, List[float]] = {}
        self.idempotency_store: Dict[str, str] = {}
        self.gemini_counts: Dict[str, int] = {}

    @property
    def is_connected(self) -> bool:
        return self._connected

    def set_connected(self, status: bool) -> None:
        self._connected = status

    async def check_rate_limit(
        self, key: str, limit: int, window_seconds: int
    ) -> Tuple[bool, int, int]:
        if not self._connected:
            raise ConnectionError("Redis connection lost.")

        now = time.time()
        clear_before = now - window_seconds
        timestamps = [t for t in self.windows.get(key, []) if t > clear_before]

        if len(timestamps) < limit:
            timestamps.append(now)
            self.windows[key] = timestamps
            return True, 0, len(timestamps)
        else:
            oldest = timestamps[0]
            retry_after = max(1, int(oldest + window_seconds - now))
            self.windows[key] = timestamps
            return False, retry_after, len(timestamps)

    async def get_idempotent_response(self, idempotency_key: str, identity: str) -> Optional[Dict[str, Any]]:
        if not self._connected:
            return None
        cache_key = f"idempotency:{identity}:{idempotency_key}"
        val = self.idempotency_store.get(cache_key)
        if val:
            return json.loads(val)
        return None

    async def set_idempotent_response(
        self, idempotency_key: str, identity: str, response_data: Dict[str, Any], ttl_seconds: int = 86400
    ) -> None:
        if not self._connected:
            return
        cache_key = f"idempotency:{identity}:{idempotency_key}"
        self.idempotency_store[cache_key] = json.dumps(response_data)

    async def check_gemini_daily_budget(self, max_daily_budget: int = 500) -> bool:
        if not self._connected:
            return True
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        current = self.gemini_counts.get(today, 0) + 1
        self.gemini_counts[today] = current
        if current > max_daily_budget:
            return False
        return True


test_app = FastAPI(title="CivicFix Rate Limiting Test App")
test_app.include_router(reports_api.router, prefix="/api/v1")


@pytest.fixture(autouse=True)
def setup_test_state():
    """Reset stores and initialize mock limiter on app.state before every test."""
    _in_memory_reports.clear()
    _in_memory_issues.clear()
    _rate_limits.clear()
    limiter = MockRateLimiter(connected=True)
    test_app.state.limiter = limiter
    yield limiter
    _in_memory_reports.clear()
    _in_memory_issues.clear()
    _rate_limits.clear()
    test_app.state.limiter = None


def create_token(user_id: str, is_anonymous: bool = False) -> str:
    payload = {
        "sub": user_id,
        "role": "anon" if is_anonymous else "authenticated",
        "aud": "authenticated",
        "is_anonymous": is_anonymous,
    }
    return jwt.encode(payload, settings.SUPABASE_SECRET_KEY, algorithm="HS256")


@pytest.mark.asyncio
async def test_redis_rate_limiting_429_and_retry_after():
    """Exceeding the rate limit returns HTTP 429 with Retry-After header."""
    user_id = "citizen-signed-in-001"
    token = create_token(user_id, is_anonymous=False)
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        # Submit 10 allowed reports for signed-in user
        for i in range(10):
            res = await client.post(
                "/api/v1/reports",
                headers=headers,
                json={
                    "image_path": f"reports/{user_id}/photo_{i}.webp",
                    "lat": 38.9784,
                    "lng": -76.4922,
                    "description": f"Test report {i}",
                },
            )
            assert res.status_code == 202, f"Expected 202 on report {i}, got {res.status_code}"

        # 11th request must exceed the 10/hour limit
        res_limit = await client.post(
            "/api/v1/reports",
            headers=headers,
            json={
                "image_path": f"reports/{user_id}/overflow.webp",
                "lat": 38.9784,
                "lng": -76.4922,
                "description": "Overflow report",
            },
        )
        assert res_limit.status_code == 429
        assert "Retry-After" in res_limit.headers
        retry_after = int(res_limit.headers["Retry-After"])
        assert retry_after > 0


@pytest.mark.asyncio
async def test_redis_rate_limiting_per_user_isolation():
    """One user reaching their quota does not affect another user."""
    user_a = "citizen-user-A"
    user_b = "citizen-user-B"
    token_a = create_token(user_a, is_anonymous=False)
    token_b = create_token(user_b, is_anonymous=False)

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        # Exhaust user A's limit
        for i in range(10):
            await client.post(
                "/api/v1/reports",
                headers={"Authorization": f"Bearer {token_a}"},
                json={"image_path": f"reports/{user_a}/img_{i}.webp", "lat": 38.9784, "lng": -76.4922},
            )

        # User A is blocked
        res_a = await client.post(
            "/api/v1/reports",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"image_path": f"reports/{user_a}/extra.webp", "lat": 38.9784, "lng": -76.4922},
        )
        assert res_a.status_code == 429

        # User B can still submit normally
        res_b = await client.post(
            "/api/v1/reports",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"image_path": f"reports/{user_b}/img_0.webp", "lat": 38.9784, "lng": -76.4922},
        )
        assert res_b.status_code == 202


@pytest.mark.asyncio
async def test_anonymous_stricter_than_signed_in():
    """Anonymous users are capped at 3/hr while signed-in users have 10/hr."""
    anon_user = "anon-citizen-999"
    token_anon = create_token(anon_user, is_anonymous=True)

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        # Anonymous user can submit 3 reports
        for i in range(3):
            res = await client.post(
                "/api/v1/reports",
                headers={"Authorization": f"Bearer {token_anon}"},
                json={"image_path": f"reports/{anon_user}/anon_{i}.webp", "lat": 38.9784, "lng": -76.4922},
            )
            assert res.status_code == 202

        # 4th anonymous report is immediately rejected with 429
        res_4 = await client.post(
            "/api/v1/reports",
            headers={"Authorization": f"Bearer {token_anon}"},
            json={"image_path": f"reports/{anon_user}/anon_3.webp", "lat": 38.9784, "lng": -76.4922},
        )
        assert res_4.status_code == 429
        assert "Allowed: 3 report(s) per hour" in res_4.json()["detail"]


@pytest.mark.asyncio
async def test_idempotent_retry_returns_same_report():
    """Retrying with identical Idempotency-Key returns exact same report ID without double incrementing."""
    user_id = "citizen-idempotent-user"
    token = create_token(user_id, is_anonymous=False)
    idempotency_key = "idemp-key-xyz-789"
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": idempotency_key,
    }

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        # 1. First submission
        res1 = await client.post(
            "/api/v1/reports",
            headers=headers,
            json={"image_path": f"reports/{user_id}/pothole.webp", "lat": 38.9784, "lng": -76.4922},
        )
        assert res1.status_code == 202
        data1 = res1.json()
        report_id1 = data1["id"]

        # 2. Duplicate submission with exact same key
        res2 = await client.post(
            "/api/v1/reports",
            headers=headers,
            json={"image_path": f"reports/{user_id}/pothole.webp", "lat": 38.9784, "lng": -76.4922},
        )
        assert res2.status_code == 202
        data2 = res2.json()

        # Must return the identical report ID and creation timestamp
        assert data2["id"] == report_id1
        assert data2["created_at"] == data1["created_at"]

        # Only 1 report should be present in memory/database
        assert len(_in_memory_reports) == 1


@pytest.mark.asyncio
async def test_redis_down_expensive_route_returns_503(setup_test_state):
    """When Redis is disconnected, fail_open=False route returns HTTP 503."""
    limiter: MockRateLimiter = setup_test_state
    limiter.set_connected(False)  # Simulate Redis outage

    user_id = "citizen-resilience-user"
    token = create_token(user_id, is_anonymous=False)

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/reports",
            headers={"Authorization": f"Bearer {token}"},
            json={"image_path": f"reports/{user_id}/pothole.webp", "lat": 38.9784, "lng": -76.4922},
        )
        assert res.status_code == 503
        assert "Rate limiting service is unavailable" in res.json()["detail"]


@pytest.mark.asyncio
async def test_daily_gemini_budget_guard(setup_test_state):
    """Daily Gemini budget cap stops enqueueing AI jobs and holds report in PENDING."""
    limiter: MockRateLimiter = setup_test_state
    user_id = "citizen-budget-test"
    token = create_token(user_id, is_anonymous=False)

    # Force daily budget to cap by setting count past threshold
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    limiter.gemini_counts[today] = settings.GEMINI_DAILY_BUDGET

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/reports",
            headers={"Authorization": f"Bearer {token}"},
            json={"image_path": f"reports/{user_id}/budget_test.webp", "lat": 38.9784, "lng": -76.4922},
        )
        assert res.status_code == 202
        data = res.json()
        assert data["status"] == "PENDING"
        assert "Daily AI triage cap reached" in data["message"]

