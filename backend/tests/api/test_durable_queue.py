"""CivicFix Phase 2 Durable Queue & Worker Tests.

Tests:
1. End-to-end report ingestion & background worker triage with mocked Gemini.
2. Duplicate enqueue rejected via _job_id deduplication.
3. Worker restart mid-job recovery via sweeper.
4. Global Gemini concurrency limit holds across concurrent workers.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from app.core.queue import enqueue_report
from app.worker import (
    process_report_job,
    acquire_global_gemini_slot,
    release_global_gemini_slot,
    metrics,
    GEMINI_MAX_CONCURRENCY,
)
from reports_api import (
    router as reports_router,
    _in_memory_reports,
    _in_memory_issues,
    _rate_limits,
)
from tests.api.test_redis_limits import MockRateLimiter, create_token


@pytest.fixture
def clean_stores():
    """Reset shared stores between tests."""
    _in_memory_reports.clear()
    _in_memory_issues.clear()
    _rate_limits.clear()
    yield
    _in_memory_reports.clear()
    _in_memory_issues.clear()
    _rate_limits.clear()


class MockArqPool:
    """Mock ARQ Redis connection pool with deduplication tracking."""

    def __init__(self):
        self.enqueued_jobs = {}
        self.enqueue_calls = []

    async def enqueue_job(self, function_name: str, *args, **kwargs):
        job_id = kwargs.get("_job_id")
        self.enqueue_calls.append({"function": function_name, "args": args, "job_id": job_id})
        if job_id and job_id in self.enqueued_jobs:
            # Duplicate job already queued or active in ARQ
            return None
        job_mock = MagicMock(job_id=job_id)
        if job_id:
            self.enqueued_jobs[job_id] = job_mock
        return job_mock


@pytest.fixture
def mock_arq_pool():
    return MockArqPool()


@pytest.fixture
def queue_test_app(mock_arq_pool):
    """FastAPI test app with both mock RateLimiter and mock ArqPool mounted."""
    app = FastAPI()
    app.include_router(reports_router, prefix="/api/v1")
    app.state.limiter = MockRateLimiter(connected=True)
    app.state.arq_pool = mock_arq_pool
    return app


@pytest.mark.asyncio
async def test_durable_queue_e2e_with_mocked_gemini(queue_test_app, mock_arq_pool, clean_stores):
    """E2E Test: Report submission returns 202, enqueues to ARQ, and worker processes successfully."""
    user_id = "test-worker-user-0001"
    token = create_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "image_path": f"reports/{user_id}/test_pothole.webp",
        "lat": 38.9784,
        "lng": -76.4922,
        "description": "Deep road crater near curb",
    }

    async with AsyncClient(
        transport=ASGITransport(app=queue_test_app), base_url="http://test"
    ) as client:
        # 1. Citizen posts report
        resp = await client.post("/api/v1/reports", json=payload, headers=headers)
        assert resp.status_code == 202
        data = resp.json()
        report_id = data["id"]
        assert data["status"] == "PENDING"

        # 2. Verify report was enqueued to ARQ pool with deduplication key
        assert len(mock_arq_pool.enqueue_calls) == 1
        assert mock_arq_pool.enqueue_calls[0]["job_id"] == f"report:{report_id}"
        assert mock_arq_pool.enqueue_calls[0]["args"] == (report_id,)

        # 3. Simulate ARQ Worker picking up and running the job with mocked Gemini
        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.decr = AsyncMock(return_value=0)
        mock_redis.expire = AsyncMock(return_value=True)

        ctx = {"redis": mock_redis, "job_id": f"report:{report_id}"}

        with patch("app.worker.call_gemini_vision", new=AsyncMock(return_value=("POTHOLE", 0.94))):
            job_result = await process_report_job(ctx, report_id)

        assert job_result["status"] == "DONE"
        assert job_result["result"] == "NEW_ISSUE"

        # 4. Verify report record in store is updated
        updated_report = _in_memory_reports[report_id]
        assert updated_report["status"] == "DONE"
        assert updated_report["category"] == "POTHOLE"
        assert updated_report["ai_confidence"] == 0.94
        assert updated_report["issue_id"] is not None

        # 5. Verify created issue
        created_issue = _in_memory_issues[updated_report["issue_id"]]
        assert created_issue["category"] == "POTHOLE"
        assert created_issue["priority_level"] == "HIGH"
        assert created_issue["status"] == "SUBMITTED"


@pytest.mark.asyncio
async def test_duplicate_enqueue_rejected(mock_arq_pool):
    """ARQ deduplication: Enqueueing the same report twice rejects duplicate job."""
    report_id = "test-dup-rep-12345"

    # First enqueue succeeds
    first_result = await enqueue_report(mock_arq_pool, report_id)
    assert first_result is True
    assert f"report:{report_id}" in mock_arq_pool.enqueued_jobs

    # Second enqueue with same report_id returns False (duplicate rejected)
    second_result = await enqueue_report(mock_arq_pool, report_id)
    assert second_result is False

    # Still only 1 entry registered in pool
    assert len(mock_arq_pool.enqueued_jobs) == 1


@pytest.mark.asyncio
async def test_worker_restart_mid_job_recovers(queue_test_app, mock_arq_pool, clean_stores):
    """Crash recovery: A report stranded in PROCESSING is recovered by sweeper and reprocessed."""
    user_id = "test-worker-user-0002"
    report_id = "stranded-report-9999"
    stale_time = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()

    # Stranded report simulates worker crashed mid-execution
    _in_memory_reports[report_id] = {
        "id": report_id,
        "user_id": user_id,
        "image_path": f"reports/{user_id}/stranded.webp",
        "lat": 38.9784,
        "lng": -76.4922,
        "description": "Stranded issue",
        "status": "PROCESSING",
        "created_at": stale_time,
        "updated_at": stale_time,
    }

    async with AsyncClient(
        transport=ASGITransport(app=queue_test_app), base_url="http://test"
    ) as client:
        # Sweeper runs
        resp = await client.post("/api/v1/reports/sweeper/recover")
        assert resp.status_code == 200
        assert resp.json()["recovered_count"] == 1

        # Verify status reset to PENDING and job re-enqueued to ARQ
        assert _in_memory_reports[report_id]["status"] == "PENDING"
        assert f"report:{report_id}" in mock_arq_pool.enqueued_jobs

        # Worker restarts and executes the job
        ctx = {"redis": None, "job_id": f"report:{report_id}"}
        with patch("app.worker.call_gemini_vision", new=AsyncMock(return_value=("STREET_LIGHT", 0.88))):
            job_result = await process_report_job(ctx, report_id)

        assert job_result["status"] == "DONE"
        assert _in_memory_reports[report_id]["status"] == "DONE"
        assert _in_memory_reports[report_id]["category"] == "STREET_LIGHT"


@pytest.mark.asyncio
async def test_global_gemini_limit_holds_with_concurrent_workers():
    """Global concurrency limit: Even with multiple workers, Gemini concurrency never exceeds cap."""
    redis_counter = 0
    active_holders = 0
    max_concurrent_holders = 0
    lock = asyncio.Lock()

    class SharedRedisSimulator:
        """Simulates Redis atomic incr/decr across multiple simulated workers."""

        async def incr(self, key):
            nonlocal redis_counter
            async with lock:
                redis_counter += 1
                return redis_counter

        async def decr(self, key):
            nonlocal redis_counter
            async with lock:
                redis_counter -= 1
                return redis_counter

        async def expire(self, key, seconds):
            return True

        async def set(self, key, val):
            nonlocal redis_counter
            async with lock:
                redis_counter = val

    shared_redis = SharedRedisSimulator()

    async def simulated_worker_task(task_id: int):
        nonlocal active_holders, max_concurrent_holders
        acquired, _ = await acquire_global_gemini_slot(shared_redis)
        assert acquired is True

        # Enter critical section (holding slot)
        async with lock:
            active_holders += 1
            if active_holders > max_concurrent_holders:
                max_concurrent_holders = active_holders

        # Simulate Gemini API latency
        await asyncio.sleep(0.05)

        # Exit critical section
        async with lock:
            active_holders -= 1

        await release_global_gemini_slot(shared_redis)

    # Launch 6 concurrent workers against a max concurrency cap of 4
    tasks = [simulated_worker_task(i) for i in range(6)]
    await asyncio.gather(*tasks)

    # Verify that at no time did active concurrent holders exceed GEMINI_MAX_CONCURRENCY (4)
    assert max_concurrent_holders <= GEMINI_MAX_CONCURRENCY
    assert max_concurrent_holders > 0
    # Final state released
    assert redis_counter == 0
    assert active_holders == 0
