"""Pytest suite for CivicFix Asynchronous Report Pipeline.

Covers:
1. HTTP 202 Accepted response on report submission
2. Foreign image_path 403 Forbidden
3. Bad coordinates 422 Unprocessable Entity
4. Rate limiting 429 Too Many Requests
5. Duplicate merge within 100m
6. Gemini Vision failure -> FAILED state
7. Sweeper recovery for timed-out processing jobs
"""

import asyncio
from datetime import datetime, timezone, timedelta
import jwt
import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from app.core.config import settings
import reports_api
from reports_api import (
    _in_memory_reports,
    _in_memory_issues,
    _rate_limits,
    run_ai_and_deduplication_pipeline,
)
from tests.api.test_redis_limits import MockRateLimiter

async_test_app = FastAPI(title="CivicFix Async Ingestion Test App")
async_test_app.include_router(reports_api.router, prefix="/api/v1")


@pytest.fixture(autouse=True)
def clean_state():
    """Reset in-memory stores and rate limits before every test."""
    _in_memory_reports.clear()
    _in_memory_issues.clear()
    _rate_limits.clear()
    async_test_app.state.limiter = MockRateLimiter(connected=True)
    yield
    _in_memory_reports.clear()
    _in_memory_issues.clear()
    _rate_limits.clear()
    async_test_app.state.limiter = None


@pytest.fixture
def auth_headers():
    """Generate mock Supabase Auth Bearer token for test citizen."""
    user_id = "test-citizen-uuid-1111"
    token = jwt.encode(
        {"sub": user_id, "role": "authenticated", "aud": "authenticated"},
        settings.SUPABASE_SECRET_KEY,
        algorithm="HS256",
    )
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


@pytest.fixture
async def async_client():
    """AsyncClient fixture for non-blocking FastAPI testing."""
    async with AsyncClient(
        transport=ASGITransport(app=async_test_app), base_url="http://test"
    ) as client:
        yield client


# ─── 1. HTTP 202 ACCEPTED TEST ────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_async_report_submission_202(async_client, auth_headers):
    """Submitting valid report returns HTTP 202 Accepted with tracking id."""
    user_id = "test-citizen-uuid-1111"
    payload = {
        "image_path": f"reports/{user_id}/damage_photo.webp",
        "lat": 38.9784,
        "lng": -76.4922,
        "description": "Pothole on Main Street",
    }
    response = await async_client.post("/api/v1/reports", json=payload, headers=auth_headers)
    assert response.status_code == 202
    data = response.json()
    assert "id" in data
    assert data["status"] == "PENDING"
    assert data["message"] == "Report accepted and queued for processing."


# ─── 2. FOREIGN IMAGE PATH 403 TEST ───────────────────────────────────────────
@pytest.mark.asyncio
async def test_foreign_image_path_403(async_client, auth_headers):
    """Attempting to use an image path belonging to another user returns 403 Forbidden."""
    payload = {
        "image_path": "reports/victim-user-id-9999/photo.webp",
        "lat": 38.9784,
        "lng": -76.4922,
        "description": "Attempted foreign file access",
    }
    response = await async_client.post("/api/v1/reports", json=payload, headers=auth_headers)
    assert response.status_code == 403
    assert "Foreign image_path forbidden" in response.json()["detail"]


# ─── 3. BAD COORDINATES 422 TEST ──────────────────────────────────────────────
@pytest.mark.asyncio
async def test_bad_coordinates_422(async_client, auth_headers):
    """Invalid latitude or longitude coordinates return 422 Unprocessable Entity."""
    user_id = "test-citizen-uuid-1111"
    payload = {
        "image_path": f"reports/{user_id}/damage_photo.webp",
        "lat": 150.0,  # Invalid latitude (> 90)
        "lng": -76.4922,
        "description": "Out of bounds coordinate",
    }
    response = await async_client.post("/api/v1/reports", json=payload, headers=auth_headers)
    assert response.status_code == 422


# ─── 4. RATE LIMITING 429 TEST ────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_rate_limiting_429(async_client, auth_headers):
    """Exceeding configured requests per minute returns HTTP 429 Too Many Requests."""
    user_id = "test-citizen-uuid-1111"
    payload = {
        "image_path": f"reports/{user_id}/flood_photo.webp",
        "lat": 38.9784,
        "lng": -76.4922,
        "description": "Burst water main",
    }

    # Saturate rate limit bucket (10 requests)
    for _ in range(10):
        res = await async_client.post("/api/v1/reports", json=payload, headers=auth_headers)
        assert res.status_code == 202

    # 11th request must trigger 429
    res = await async_client.post("/api/v1/reports", json=payload, headers=auth_headers)
    assert res.status_code == 429
    assert "Rate limit exceeded" in res.json()["detail"]


# ─── 5. DUPLICATE MERGE WITHIN 100M TEST ──────────────────────────────────────
@pytest.mark.asyncio
async def test_duplicate_merge_within_100m():
    """Reports within 100 meters merge into existing issue and increment duplicate count."""
    user_id = "test-citizen-uuid-1111"

    # Report 1 at State Circle, Annapolis
    rep1_id = "rep-0001"
    _in_memory_reports[rep1_id] = {
        "id": rep1_id,
        "user_id": user_id,
        "image_path": f"reports/{user_id}/1.webp",
        "lat": 38.9784,
        "lng": -76.4922,
        "description": "Pothole on State Circle",
        "status": "PENDING",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await run_ai_and_deduplication_pipeline(rep1_id)
    assert _in_memory_reports[rep1_id]["status"] == "DONE"
    issue_id = _in_memory_reports[rep1_id]["issue_id"]
    assert issue_id is not None
    assert _in_memory_issues[issue_id]["duplicate_count"] == 0

    # Report 2 ~45 meters away (38.9787, -76.4925)
    rep2_id = "rep-0002"
    _in_memory_reports[rep2_id] = {
        "id": rep2_id,
        "user_id": user_id,
        "image_path": f"reports/{user_id}/2.webp",
        "lat": 38.9787,
        "lng": -76.4925,
        "description": "Road hazard nearby",
        "status": "PENDING",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await run_ai_and_deduplication_pipeline(rep2_id)
    assert _in_memory_reports[rep2_id]["status"] == "DONE"
    assert _in_memory_reports[rep2_id]["is_duplicate"] is True
    assert _in_memory_reports[rep2_id]["issue_id"] == issue_id
    assert _in_memory_issues[issue_id]["duplicate_count"] == 1


# ─── 6. GEMINI FAILURE -> FAILED STATE TEST ───────────────────────────────────
@pytest.mark.asyncio
async def test_gemini_failure_transitions_to_failed(monkeypatch):
    """When Gemini Vision fails, the report transitions to status FAILED with error message."""
    user_id = "test-citizen-uuid-1111"
    rep_id = "rep-fail-0001"

    # Mock Gemini failure
    async def mock_failing_gemini(*args, **kwargs):
        raise RuntimeError("Google Gemini API quota exceeded or service 503 unavailable.")

    monkeypatch.setattr(reports_api, "call_gemini_vision", mock_failing_gemini)

    _in_memory_reports[rep_id] = {
        "id": rep_id,
        "user_id": user_id,
        "image_path": f"reports/{user_id}/fail.webp",
        "lat": 38.9784,
        "lng": -76.4922,
        "description": "Will fail",
        "status": "PENDING",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    await run_ai_and_deduplication_pipeline(rep_id)

    assert _in_memory_reports[rep_id]["status"] == "FAILED"
    assert "Google Gemini API quota exceeded" in _in_memory_reports[rep_id]["error_message"]


# ─── 7. SWEEPER RECOVERY FOR STALE JOBS TEST ──────────────────────────────────
@pytest.mark.asyncio
async def test_sweeper_recovers_stale_processing_jobs(async_client):
    """Reports stuck in PROCESSING for > 10 minutes are automatically transitioned to FAILED."""
    stale_id = "rep-stale-0001"
    old_time = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()

    _in_memory_reports[stale_id] = {
        "id": stale_id,
        "user_id": "test-citizen-uuid-1111",
        "image_path": "reports/test-citizen-uuid-1111/stale.webp",
        "lat": 38.9784,
        "lng": -76.4922,
        "status": "PROCESSING",
        "created_at": old_time,
        "updated_at": old_time,
    }

    response = await async_client.post("/api/v1/reports/sweeper/recover")
    assert response.status_code == 200
    data = response.json()
    assert data["recovered_count"] == 1
    assert _in_memory_reports[stale_id]["status"] == "FAILED"
    assert "timed out" in _in_memory_reports[stale_id]["error_message"]


# ─── 8. GET /issues/{id}/proofs FOR RESOLVED ISSUES ONLY ──────────────────────
from app.api.issues import router as issues_router

async_test_issues_app = FastAPI()
async_test_issues_app.include_router(issues_router, prefix="/api/v1")


@pytest.mark.asyncio
async def test_issue_proofs_requires_resolved(monkeypatch):
    """GET /issues/{id}/proofs returns 400 Bad Request if issue is not RESOLVED, and 200 with signed URLs if RESOLVED."""
    from app.services.issue_service import issue_service

    class MockIssue:
        id = 101
        status = "IN_PROGRESS"
        before_photo_path = "proofs/before_101.webp"
        after_photo_path = None

    # 1. Non-resolved issue should be rejected with 400
    async def mock_get_issue(db, issue_id):
        return MockIssue()

    monkeypatch.setattr(issue_service, "get_issue", mock_get_issue)

    async with AsyncClient(
        transport=ASGITransport(app=async_test_issues_app), base_url="http://test"
    ) as client:
        res = await client.get("/api/v1/issues/101/proofs")
        assert res.status_code == 400
        assert "RESOLVED" in res.json()["detail"]

        # 2. Resolved issue should succeed and return signed URLs
        MockIssue.status = "RESOLVED"
        MockIssue.after_photo_path = "proofs/after_101.webp"

        res2 = await client.get("/api/v1/issues/101/proofs")
        assert res2.status_code == 200
        data = res2.json()
        assert data["status"] == "RESOLVED"
        assert "storage/v1/object/sign/proofs" in data["before_photo_url"]
        assert "storage/v1/object/sign/proofs" in data["after_photo_url"]
        assert data["expires_in"] == 900

