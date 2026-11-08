"""CivicFix Phase 4: Resilience & Circuit Breaker Tests.

Tests:
1. Gemini Circuit Breaker: After N failures, circuit trips to OPEN.
2. PENDING_MANUAL Triage: Tripped circuit transitions reports to PENDING_MANUAL for dispatcher queue.
3. Circuit Breaker Recovery: Cooldown expiration allows probe; success resets circuit to CLOSED.
4. Local JWKS Verification: Validates tokens, handles anonymous flags, rejects expired/tampered tokens.
5. Outbound Call Timeouts: Enforces strict timeout limits on slow external calls.
6. Retries with Jitter: Retries transient errors up to bound with jittered backoff.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch
import jwt
import pytest
from fastapi import HTTPException

from app.core.circuit_breaker import (
    CircuitBreaker,
    gemini_circuit_breaker,
    call_with_timeout,
    retry_with_jitter,
)
from app.core.jwks import verify_supabase_jwt
from app.worker import process_report_job
from app.models.report import ReportStatus
from reports_api import (
    _in_memory_reports,
    _in_memory_issues,
)
from tests.api.test_redis_limits import create_token


@pytest.fixture
def clean_state():
    _in_memory_reports.clear()
    _in_memory_issues.clear()
    yield
    _in_memory_reports.clear()
    _in_memory_issues.clear()


# ─── 1. CIRCUIT BREAKER TRIPPING & COOLDOWN TESTS ───────────────────────────
@pytest.mark.asyncio
async def test_circuit_breaker_trips_to_open_after_n_failures():
    """Circuit breaker transitions from CLOSED to OPEN after failure_threshold."""
    cb = CircuitBreaker(name="test_cb", failure_threshold=3, cooldown_seconds=1.0)

    # Initial state: CLOSED
    assert await cb.can_execute() is True

    # 1st and 2nd failures
    tripped1 = await cb.record_failure()
    assert tripped1 is False
    assert await cb.can_execute() is True

    tripped2 = await cb.record_failure()
    assert tripped2 is False
    assert await cb.can_execute() is True

    # 3rd failure: Trips circuit to OPEN
    tripped3 = await cb.record_failure()
    assert tripped3 is True
    # In OPEN state, can_execute returns False (fast-fail)
    assert await cb.can_execute() is False


@pytest.mark.asyncio
async def test_circuit_breaker_recovers_after_cooldown():
    """After cooldown period elapses, circuit enters HALF_OPEN and resets on success."""
    cb = CircuitBreaker(
        name="test_recover_cb", failure_threshold=2, cooldown_seconds=0.1
    )

    # Trip to OPEN
    await cb.record_failure()
    await cb.record_failure()
    assert await cb.can_execute() is False

    # Wait for cooldown to expire
    await asyncio.sleep(0.12)

    # Probing allowed in HALF_OPEN
    assert await cb.can_execute() is True

    # Success resets to CLOSED
    await cb.record_success()
    assert await cb.can_execute() is True
    assert cb._local_failures == 0


# ─── 2. PENDING_MANUAL TRIAGE IN WORKER TEST ────────────────────────────────
@pytest.mark.asyncio
async def test_worker_triages_to_pending_manual_when_circuit_open(clean_state):
    """When Gemini circuit breaker is OPEN, worker marks report PENDING_MANUAL for dispatcher queue."""
    report_id = "rep-circuit-open-001"
    _in_memory_reports[report_id] = {
        "id": report_id,
        "user_id": "citizen-123",
        "image_path": "reports/citizen-123/pothole.webp",
        "lat": 38.9784,
        "lng": -76.4922,
        "description": "Street crater",
        "status": "PENDING",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    # Force circuit breaker to OPEN state
    with patch.object(
        gemini_circuit_breaker, "can_execute", new=AsyncMock(return_value=False)
    ):
        ctx = {"redis": None, "job_id": f"report:{report_id}"}
        result = await process_report_job(ctx, report_id)

    assert result["status"] == "PENDING_MANUAL"
    assert result["reason"] == "CIRCUIT_BREAKER_OPEN"

    # Verify report record is triaged for dispatcher queue
    report = _in_memory_reports[report_id]
    assert report["status"] == "PENDING_MANUAL"
    assert "circuit breaker is OPEN" in report["error_message"]
    # Check that PENDING_MANUAL exists in ReportStatus enum
    assert ReportStatus.PENDING_MANUAL.value == "PENDING_MANUAL"


# ─── 3. LOCAL JWT VERIFICATION TESTS ─────────────────────────────────────────
def test_local_jwt_verification_success():
    """HMAC and asymmetric local JWT verification extracts identity subject without network call."""
    user_id = "test-citizen-uuid-9999"
    token = create_token(user_id=user_id, is_anonymous=False)

    payload = verify_supabase_jwt(token)
    assert payload["sub"] == user_id
    assert payload["role"] == "authenticated"


def test_local_jwt_verification_rejects_expired():
    """Expired token is rejected with HTTP 401."""
    import jwt
    from app.core.config import settings

    user_id = "expired-user"
    expired_payload = {
        "sub": user_id,
        "role": "authenticated",
        "exp": int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()),
    }
    expired_token = jwt.encode(
        expired_payload, settings.SUPABASE_SECRET_KEY, algorithm="HS256"
    )

    with pytest.raises(HTTPException) as exc_info:
        verify_supabase_jwt(expired_token)
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


def test_local_jwt_verification_rejects_tampered_signature():
    """Tampered token signature is rejected with HTTP 401."""
    # Sign token with an unauthorized key: valid base64, but signature verification fails
    tampered = jwt.encode(
        {"sub": "legit-user", "aud": "authenticated"},
        "unauthorized-attacker-secret-key-32b!",
        algorithm="HS256",
    )

    with pytest.raises(HTTPException) as exc_info:
        verify_supabase_jwt(tampered)
    assert exc_info.value.status_code == 401
    assert any(
        phrase in exc_info.value.detail.lower()
        for phrase in ("verification failed", "malformed")
    )


# ─── 4. OUTBOUND CALL TIMEOUTS & RETRIES WITH JITTER TESTS ──────────────────
@pytest.mark.asyncio
async def test_call_with_timeout_enforces_limit():
    """call_with_timeout raises TimeoutError when external call exceeds deadline."""

    async def slow_external_api():
        await asyncio.sleep(0.2)
        return "slow_success"

    with pytest.raises(TimeoutError) as exc_info:
        await call_with_timeout(slow_external_api(), timeout_seconds=0.05)
    assert "timed out after 0.05 seconds" in str(exc_info.value)


@pytest.mark.asyncio
async def test_retry_with_jitter_recovers_transient_failure():
    """retry_with_jitter retries transient errors and returns result on eventual success."""
    attempts = 0

    async def flaky_service():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ConnectionError(f"Transient network glitch attempt {attempts}")
        return "success_recovered"

    result = await retry_with_jitter(
        flaky_service,
        max_retries=3,
        base_delay=0.01,
        max_delay=0.05,
        retryable_exceptions=(ConnectionError,),
    )

    assert result == "success_recovered"
    assert attempts == 3
