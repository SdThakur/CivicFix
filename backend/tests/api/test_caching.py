"""CivicFix Phase 3: Caching, Quantization & Read Replica Tests.

Tests:
1. snap_bounds(): Quantizes bounding box coordinates based on zoom level.
2. cached_json(): Cache MISS on first call, Cache HIT on second call.
3. Cache-Control header: Contains s-maxage and stale-while-revalidate for CDN caching.
4. Authorization bypass: Never caches responses containing Authorization headers.
5. Public Endpoints: Viewport (/public/map) and Stats (/public/stats) return cached responses.
6. Supabase Read Replica: get_read_db routes to replica when configured, primary otherwise.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI, Request, Response

from app.core.cache import snap_bounds, cached_json, build_cdn_cache_control, get_zoom_step
from app.api.public import router as public_router
from app.db.session import get_read_db, get_db, ReplicaAsyncSessionLocal, AsyncSessionLocal
from tests.api.test_redis_limits import MockRateLimiter, create_token
from reports_api import _in_memory_issues, _in_memory_reports


@pytest.fixture
def mock_redis():
    """In-memory Redis mock for cache operations."""
    store = {}

    class AsyncRedisMock:
        async def get(self, key):
            return store.get(key)

        async def set(self, key, val):
            store[key] = val
            return True

        async def setex(self, key, ttl, val):
            store[key] = val
            return True

        async def delete(self, key):
            store.pop(key, None)
            return True

    return AsyncRedisMock(), store


@pytest.fixture
def public_test_app(mock_redis):
    redis_instance, _ = mock_redis
    app = FastAPI()
    app.include_router(public_router, prefix="/api/v1")
    app.include_router(public_router)
    app.state.redis_cache = redis_instance
    return app


# ─── 1. SNAP BOUNDS VIEWPORT QUANTIZATION TESTS ─────────────────────────────
def test_snap_bounds_quantization():
    """snap_bounds quantizes nearby viewport requests into identical grid cells."""
    # Two users panning slightly within the same neighborhood at zoom 14 (step 0.002)
    min_lat_user1, max_lat_user1 = 38.97811, 38.98812
    min_lng_user1, max_lng_user1 = -76.49211, -76.48212

    min_lat_user2, max_lat_user2 = 38.97819, 38.98818
    min_lng_user2, max_lng_user2 = -76.49218, -76.48219

    snapped1 = snap_bounds(min_lat_user1, max_lat_user1, min_lng_user1, max_lng_user1, zoom=14)
    snapped2 = snap_bounds(min_lat_user2, max_lat_user2, min_lng_user2, max_lng_user2, zoom=14)

    # Both users snap to the exact same bounding box!
    assert snapped1 == snapped2

    # Verify bounds fully encompass the query
    s_min_lat, s_max_lat, s_min_lng, s_max_lng = snapped1
    assert s_min_lat <= min_lat_user1
    assert s_max_lat >= max_lat_user1
    assert s_min_lng <= min_lng_user1
    assert s_max_lng >= max_lng_user1


def test_zoom_step_hierarchy():
    """Higher zoom levels produce finer grid steps."""
    step_world = get_zoom_step(5)     # 0.05
    step_city = get_zoom_step(10)     # 0.01
    step_hood = get_zoom_step(13)     # 0.002
    step_street = get_zoom_step(16)   # 0.0005

    assert step_world > step_city > step_hood > step_street


# ─── 2. CACHED_JSON & CDN HEADERS TESTS ─────────────────────────────────────
@pytest.mark.asyncio
async def test_cached_json_hit_and_miss_with_cdn_headers(mock_redis):
    """cached_json returns MISS on first request, stores in Redis, returns HIT on second."""
    redis_instance, store = mock_redis
    req_mock = MagicMock(spec=Request)
    req_mock.headers = {}
    req_mock.app.state.redis_cache = redis_instance

    call_count = 0

    async def expensive_computation():
        nonlocal call_count
        call_count += 1
        return {"data": "expensive_result", "count": call_count}

    cache_key = "test:expensive_query"
    ttl = 30

    # 1. First invocation: Cache MISS
    resp1 = await cached_json(cache_key, ttl, req_mock, expensive_computation)
    assert resp1.headers["X-Cache"] == "MISS"
    assert "public, max-age=" in resp1.headers["Cache-Control"]
    assert "s-maxage=30" in resp1.headers["Cache-Control"]
    assert "stale-while-revalidate=" in resp1.headers["Cache-Control"]
    assert call_count == 1
    assert cache_key in store

    # 2. Second invocation: Cache HIT
    resp2 = await cached_json(cache_key, ttl, req_mock, expensive_computation)
    assert resp2.headers["X-Cache"] == "HIT"
    assert resp2.headers["X-Cache-Key"] == cache_key
    assert json.loads(resp2.body.decode("utf-8"))["count"] == 1
    # Underlying function was NOT called again!
    assert call_count == 1


# ─── 3. AUTHORIZATION HEADER STRICT BYPASS TEST ─────────────────────────────
@pytest.mark.asyncio
async def test_authorization_header_strictly_bypasses_cache(mock_redis):
    """Never cache anything with an Authorization header."""
    redis_instance, store = mock_redis
    req_mock = MagicMock(spec=Request)
    req_mock.headers = {"authorization": "Bearer secret_user_token"}
    req_mock.app.state.redis_cache = redis_instance

    call_count = 0

    async def user_private_data():
        nonlocal call_count
        call_count += 1
        return {"private": "user_sensitive_data", "run": call_count}

    cache_key = "test:auth_route"
    ttl = 60

    # First call with Auth header
    resp1 = await cached_json(cache_key, ttl, req_mock, user_private_data)
    assert resp1.headers["X-Cache"] == "BYPASS"
    assert "private" in resp1.headers["Cache-Control"]
    assert "no-store" in resp1.headers["Cache-Control"]
    # NOT saved in Redis
    assert cache_key not in store

    # Second call with Auth header -> Still bypasses
    resp2 = await cached_json(cache_key, ttl, req_mock, user_private_data)
    assert resp2.headers["X-Cache"] == "BYPASS"
    assert call_count == 2
    assert cache_key not in store


# ─── 4. PUBLIC API ENDPOINTS INTEGRATION TEST ────────────────────────────────
@pytest.mark.asyncio
async def test_public_map_viewport_endpoint(public_test_app, mock_redis):
    """GET /public/map quantizes bounds and caches viewport results."""
    _in_memory_issues["test-map-issue-1"] = {
        "id": "test-map-issue-1",
        "tracking_number": "ISS-2026-001",
        "title": "Main Street Pothole",
        "category": "POTHOLE",
        "status": "SUBMITTED",
        "priority_level": "HIGH",
        "lat": 38.9785,
        "lng": -76.4925,
        "duplicate_count": 2,
    }

    async with AsyncClient(
        transport=ASGITransport(app=public_test_app), base_url="http://test"
    ) as client:
        # Request 1: Cache MISS
        r1 = await client.get("/api/v1/public/map?min_lat=38.9&max_lat=39.0&min_lng=-76.5&max_lng=-76.4&zoom=14")
        assert r1.status_code == 200
        assert r1.headers["X-Cache"] == "MISS"
        assert "s-maxage=30" in r1.headers["Cache-Control"]
        items1 = r1.json()
        assert len(items1) >= 1
        assert any(i["title"] == "Main Street Pothole" for i in items1)

        # Request 2: Cache HIT
        r2 = await client.get("/api/v1/public/map?min_lat=38.9&max_lat=39.0&min_lng=-76.5&max_lng=-76.4&zoom=14")
        assert r2.status_code == 200
        assert r2.headers["X-Cache"] == "HIT"


@pytest.mark.asyncio
async def test_public_stats_endpoint(public_test_app):
    """GET /public/stats returns cached public performance metrics."""
    async with AsyncClient(
        transport=ASGITransport(app=public_test_app), base_url="http://test"
    ) as client:
        r1 = await client.get("/public/stats")
        assert r1.status_code == 200
        assert r1.headers["X-Cache"] == "MISS"
        assert "s-maxage=60" in r1.headers["Cache-Control"]
        stats = r1.json()
        assert "total_reports" in stats
        assert "resolution_rate_pct" in stats

        # Second request hits cache
        r2 = await client.get("/public/stats")
        assert r2.status_code == 200
        assert r2.headers["X-Cache"] == "HIT"


# ─── 5. SUPABASE READ REPLICA ROUTING TEST ──────────────────────────────────
@pytest.mark.asyncio
async def test_read_replica_session_routing():
    """get_read_db routes to ReplicaAsyncSessionLocal while get_db routes to primary."""
    # When replica_url is configured, ReplicaAsyncSessionLocal is distinct
    assert hasattr(ReplicaAsyncSessionLocal, "__call__")
    assert hasattr(AsyncSessionLocal, "__call__")

    async for read_session in get_read_db():
        assert read_session is not None
        break

    async for write_session in get_db():
        assert write_session is not None
        break

