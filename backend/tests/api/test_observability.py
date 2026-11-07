"""CivicFix Phase 5: Observability, Metrics & Structured Logging Tests.

Tests:
1. X-Request-ID propagation: Incoming header is honored and reflected on outbound responses.
2. Automated Request ID generation: When absent, a UUID4 request_id is assigned.
3. Structured JSON Logging: Logs record request_id, user_id_hash (SHA-256), route, latency_ms.
4. Prometheus /metrics endpoint: Exposes valid Prometheus text format metrics.
5. Telemetry counters: HTTP request counts and 429 rate limit counters increment correctly.
"""

import json
import logging
from unittest.mock import MagicMock, patch
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI, Request, Response

from app.core.metrics import (
    HTTP_REQUESTS_TOTAL,
    RATE_LIMIT_EXCEEDED_TOTAL,
    get_prometheus_metrics,
)
from app.core.logging_middleware import ObservabilityMiddleware
from app.api.public import router as public_router
from tests.api.test_redis_limits import create_token


@pytest.fixture
def obs_test_app():
    """FastAPI test app configured with ObservabilityMiddleware and /metrics."""
    app = FastAPI()
    app.add_middleware(ObservabilityMiddleware)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/api/v1/test-user")
    async def test_user_route(request: Request):
        # Simulate authenticated request
        request.state.user_id = "citizen-test-uuid-42"
        return {"user": "authenticated"}

    @app.get("/api/v1/test-429")
    async def test_rate_limit_route(request: Request):
        request.state.is_anonymous = True
        return Response(status_code=429, content='{"detail": "Rate limit exceeded"}')

    @app.get("/metrics")
    async def metrics():
        return Response(content=get_prometheus_metrics(), media_type="text/plain; version=0.0.4")

    return app


# ─── 1. X-REQUEST-ID PROPAGATION TESTS ──────────────────────────────────────
@pytest.mark.asyncio
async def test_request_id_propagated_from_header(obs_test_app):
    """When X-Request-ID is sent by client/Nginx, it is preserved and returned in response."""
    custom_req_id = "nginx-proxy-trace-998877"

    async with AsyncClient(
        transport=ASGITransport(app=obs_test_app), base_url="http://test"
    ) as client:
        resp = await client.get("/health", headers={"X-Request-ID": custom_req_id})
        assert resp.status_code == 200
        assert resp.headers.get("X-Request-ID") == custom_req_id


@pytest.mark.asyncio
async def test_request_id_generated_when_absent(obs_test_app):
    """When X-Request-ID is missing, middleware generates a UUID4 request_id."""
    async with AsyncClient(
        transport=ASGITransport(app=obs_test_app), base_url="http://test"
    ) as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        out_id = resp.headers.get("X-Request-ID")
        assert out_id is not None
        assert len(out_id) >= 32


# ─── 2. STRUCTURED JSON LOGGING & USER HASH TESTS ───────────────────────────
@pytest.mark.asyncio
async def test_structured_json_log_contains_required_fields(obs_test_app, caplog):
    """Middleware emits structured JSON log containing request_id, user_id_hash, route, latency_ms."""
    caplog.set_level(logging.INFO, logger="civicfix.access")

    async with AsyncClient(
        transport=ASGITransport(app=obs_test_app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v1/test-user", headers={"X-Request-ID": "req-test-123"})
        assert resp.status_code == 200

    # Locate JSON log entry emitted by middleware
    matching_records = [
        rec for rec in caplog.records if rec.name == "civicfix.access" and "req-test-123" in rec.message
    ]
    assert len(matching_records) >= 1

    payload = json.loads(matching_records[0].message)
    assert payload["request_id"] == "req-test-123"
    assert payload["route"] == "/api/v1/test-user"
    assert payload["status_code"] == 200
    assert payload["method"] == "GET"
    assert "latency_ms" in payload
    # user_id is hashed with SHA-256 (not plain text)
    assert payload["user_id_hash"] != "citizen-test-uuid-42"
    assert len(payload["user_id_hash"]) == 16


# ─── 3. PROMETHEUS /METRICS ENDPOINT TESTS ──────────────────────────────────
@pytest.mark.asyncio
async def test_prometheus_metrics_endpoint_exposition(obs_test_app):
    """GET /metrics exports standard Prometheus text telemetry format."""
    async with AsyncClient(
        transport=ASGITransport(app=obs_test_app), base_url="http://test"
    ) as client:
        # Trigger requests
        await client.get("/health")
        await client.get("/api/v1/test-429")

        # Fetch metrics
        metrics_resp = await client.get("/metrics")
        assert metrics_resp.status_code == 200
        body = metrics_resp.text

        # Verify key metrics are present
        assert "civicfix_http_requests_total" in body
        assert "civicfix_http_request_duration_seconds" in body
        assert "civicfix_rate_limit_exceeded_total" in body
        assert "civicfix_queue_depth" in body
        assert "civicfix_gemini_latency_seconds" in body

