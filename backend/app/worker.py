"""CivicFix ARQ Worker Engine for Asynchronous AI Triage & Deduplication.

Features:
- Configurable concurrency via WORKER_CONCURRENCY environment variable
- Graceful shutdown handling
- Structured JSON logging with report_id context
- Operational telemetry: queue depth, job latency, failures, and Gemini wait time
- Distributed Redis semaphore ensuring global Gemini API limits hold across multiple workers
- Safe recovery of stranded or restarted jobs
"""

import asyncio
from datetime import datetime, timezone
import json
import logging
import os
import time
from typing import Any, Dict, Optional, Tuple
import uuid

from arq.connections import ArqRedis, RedisSettings
from app.core.config import settings
from app.core.queue import get_redis_settings
from app.core.circuit_breaker import gemini_circuit_breaker, call_with_timeout
from reports_api import (
    _in_memory_reports,
    _in_memory_issues,
    haversine_distance_meters,
    call_gemini_vision,
)

logger = logging.getLogger("civicfix.worker")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Operational Telemetry Metrics Store
class WorkerMetrics:
    def __init__(self):
        self.jobs_completed = 0
        self.failures_count = 0
        self.total_latency_ms = 0.0
        self.total_gemini_wait_ms = 0.0

    def record_success(self, latency_ms: float, gemini_wait_ms: float):
        self.jobs_completed += 1
        self.total_latency_ms += latency_ms
        self.total_gemini_wait_ms += gemini_wait_ms

    def record_failure(self):
        self.failures_count += 1

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / max(1, self.jobs_completed)

    @property
    def avg_gemini_wait_ms(self) -> float:
        return self.total_gemini_wait_ms / max(1, self.jobs_completed)


metrics = WorkerMetrics()

# Global distributed Gemini concurrency limit across all worker replicas
GEMINI_MAX_CONCURRENCY = int(os.getenv("GEMINI_MAX_CONCURRENCY", "4"))
GEMINI_ACQUIRE_TIMEOUT = float(os.getenv("GEMINI_ACQUIRE_TIMEOUT", "15.0"))


async def acquire_global_gemini_slot(redis_client: Optional[Any]) -> Tuple[bool, float]:
    """Acquire a global Gemini concurrency token from Redis across all worker replicas.

    Returns (acquired: bool, wait_time_ms: float).
    """
    if redis_client is None:
        return True, 0.0

    start_time = time.time()
    semaphore_key = "gemini:active_concurrency"

    while (time.time() - start_time) < GEMINI_ACQUIRE_TIMEOUT:
        try:
            # Atomic increment
            active = await redis_client.incr(semaphore_key)
            if active == 1:
                # Set safety expiration so a crashed worker never permanently locks the semaphore
                await redis_client.expire(semaphore_key, 30)

            if active <= GEMINI_MAX_CONCURRENCY:
                wait_time_ms = (time.time() - start_time) * 1000.0
                return True, wait_time_ms

            # Concurrency limit reached: decrement and backoff
            await redis_client.decr(semaphore_key)
            await asyncio.sleep(0.05)
        except Exception as e:
            logger.warning(f"Error acquiring global Gemini slot: {e}")
            return True, (time.time() - start_time) * 1000.0

    logger.warning("Timed out waiting for global Gemini concurrency slot.")
    return False, (time.time() - start_time) * 1000.0


async def release_global_gemini_slot(redis_client: Optional[Any]) -> None:
    """Release global Gemini concurrency slot in Redis."""
    if redis_client is None:
        return
    try:
        semaphore_key = "gemini:active_concurrency"
        val = await redis_client.decr(semaphore_key)
        if val < 0:
            await redis_client.set(semaphore_key, 0)
    except Exception as e:
        logger.warning(f"Error releasing global Gemini slot: {e}")


def structured_log(event: str, report_id: str, **kwargs: Any) -> None:
    """Emit JSON structured log for centralized log aggregation."""
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "report_id": report_id,
        **kwargs,
    }
    logger.info(json.dumps(payload))


async def process_report_job(ctx: Dict[str, Any], report_id: str) -> Dict[str, Any]:
    """ARQ Worker Job: Execute AI triage and 100m spatial deduplication for a report."""
    job_start = time.time()
    redis_client = ctx.get("redis")

    structured_log("job_started", report_id, job_id=ctx.get("job_id"))

    # Fetch report from in-memory or database
    report = _in_memory_reports.get(report_id)
    if not report:
        structured_log("job_error", report_id, error="Report not found in storage.")
        metrics.record_failure()
        return {"status": "NOT_FOUND", "report_id": report_id}

    # Check Gemini Circuit Breaker before processing
    can_execute = await gemini_circuit_breaker.can_execute(redis_client)
    if not can_execute:
        report["status"] = "PENDING_MANUAL"
        report["error_message"] = "Gemini AI circuit breaker is OPEN. Triaged to dispatcher queue."
        report["updated_at"] = datetime.now(timezone.utc).isoformat()
        metrics.record_failure()
        duration_ms = (time.time() - job_start) * 1000.0
        structured_log(
            "circuit_breaker_open",
            report_id,
            status="PENDING_MANUAL",
            duration_ms=round(duration_ms, 2),
        )
        return {"status": "PENDING_MANUAL", "reason": "CIRCUIT_BREAKER_OPEN"}

    # Transition to PROCESSING
    report["status"] = "PROCESSING"
    report["updated_at"] = datetime.now(timezone.utc).isoformat()

    gemini_wait_ms = 0.0
    try:
        # 1. Acquire global Gemini concurrency slot across workers
        acquired, wait_ms = await acquire_global_gemini_slot(redis_client)
        gemini_wait_ms = wait_ms

        try:
            # 2. Call Gemini Vision AI with timeout protection
            ai_category, ai_confidence = await call_with_timeout(
                call_gemini_vision(report["image_path"], report.get("description")),
                timeout_seconds=15.0,
            )
            await gemini_circuit_breaker.record_success(redis_client)
        except Exception as gemini_err:
            tripped = await gemini_circuit_breaker.record_failure(redis_client)
            if tripped:
                report["status"] = "PENDING_MANUAL"
                report["error_message"] = f"Circuit breaker tripped on Gemini error: {gemini_err}. Triaged to dispatcher queue."
                report["updated_at"] = datetime.now(timezone.utc).isoformat()
                metrics.record_failure()
                duration_ms = (time.time() - job_start) * 1000.0
                structured_log(
                    "circuit_breaker_tripped",
                    report_id,
                    status="PENDING_MANUAL",
                    error=str(gemini_err),
                    duration_ms=round(duration_ms, 2),
                )
                return {"status": "PENDING_MANUAL", "error": str(gemini_err)}
            raise gemini_err
        finally:
            await release_global_gemini_slot(redis_client)

        report["category"] = ai_category
        report["ai_confidence"] = ai_confidence

        # 3. Spatial Deduplication (100 meter threshold)
        matched_issue_id = None
        for issue_id, issue in _in_memory_issues.items():
            if issue.get("status") in ("RESOLVED", "CLOSED", "CANCELLED"):
                continue
            dist = haversine_distance_meters(report["lat"], report["lng"], issue["lat"], issue["lng"])
            if dist <= 100.0:
                matched_issue_id = issue_id
                break

        now_str = datetime.now(timezone.utc).isoformat()
        if matched_issue_id:
            # Merge duplicate
            issue = _in_memory_issues[matched_issue_id]
            issue["duplicate_count"] = issue.get("duplicate_count", 0) + 1
            issue["priority_score"] = min(100.0, issue.get("priority_score", 50.0) + 5.0)

            report["is_duplicate"] = True
            report["issue_id"] = matched_issue_id
            report["status"] = "DONE"
            report["updated_at"] = now_str

            duration_ms = (time.time() - job_start) * 1000.0
            metrics.record_success(duration_ms, gemini_wait_ms)
            structured_log(
                "job_completed",
                report_id,
                result="DUPLICATE_MERGED",
                matched_issue_id=matched_issue_id,
                duration_ms=round(duration_ms, 2),
                gemini_wait_ms=round(gemini_wait_ms, 2),
            )
            return {"status": "DONE", "result": "DUPLICATE", "issue_id": matched_issue_id}
        else:
            # Create new issue
            new_issue_id = str(uuid.uuid4())
            tracking_num = f"ISS-{datetime.now(timezone.utc).strftime('%Y')}-{new_issue_id[:5].upper()}"
            _in_memory_issues[new_issue_id] = {
                "id": new_issue_id,
                "tracking_number": tracking_num,
                "title": f"{ai_category} on Public Right-of-Way",
                "category": ai_category,
                "description": report.get("description"),
                "status": "SUBMITTED",
                "priority_score": round(min(100.0, 50.0 + (ai_confidence * 30.0)), 2),
                "priority_level": "HIGH" if ai_confidence > 0.8 else "MEDIUM",
                "lat": report["lat"],
                "lng": report["lng"],
                "upvotes": 0,
                "duplicate_count": 0,
                "before_photo_path": report["image_path"],
                "created_at": now_str,
                "updated_at": now_str,
            }

            report["issue_id"] = new_issue_id
            report["status"] = "DONE"
            report["updated_at"] = now_str

            duration_ms = (time.time() - job_start) * 1000.0
            metrics.record_success(duration_ms, gemini_wait_ms)
            structured_log(
                "job_completed",
                report_id,
                result="ISSUE_CREATED",
                issue_id=new_issue_id,
                duration_ms=round(duration_ms, 2),
                gemini_wait_ms=round(gemini_wait_ms, 2),
            )
            return {"status": "DONE", "result": "NEW_ISSUE", "issue_id": new_issue_id}

    except Exception as e:
        report["status"] = "FAILED"
        report["error_message"] = str(e)
        report["updated_at"] = datetime.now(timezone.utc).isoformat()
        metrics.record_failure()
        duration_ms = (time.time() - job_start) * 1000.0
        structured_log(
            "job_failed",
            report_id,
            error=str(e),
            duration_ms=round(duration_ms, 2),
            gemini_wait_ms=round(gemini_wait_ms, 2),
        )
        return {"status": "FAILED", "error": str(e)}


async def startup(ctx: Dict[str, Any]) -> None:
    """Worker lifecycle startup hook."""
    logger.info("CivicFix ARQ Worker starting up. Concurrency: %s", os.getenv("WORKER_CONCURRENCY", "10"))
    # Reset local gemini concurrency semaphore if freshly starting
    redis_client = ctx.get("redis")
    if redis_client:
        await redis_client.set("gemini:active_concurrency", 0)


async def shutdown(ctx: Dict[str, Any]) -> None:
    """Worker lifecycle graceful shutdown hook."""
    logger.info("CivicFix ARQ Worker shutting down gracefully. In-flight jobs completing...")
    redis_client = ctx.get("redis")
    if redis_client:
        await redis_client.set("gemini:active_concurrency", 0)


class WorkerSettings:
    """ARQ Worker configuration class."""

    functions = [process_report_job]
    redis_settings = get_redis_settings()
    max_jobs = int(os.getenv("WORKER_CONCURRENCY", "10"))
    job_timeout = int(os.getenv("WORKER_JOB_TIMEOUT", "60"))
    on_startup = startup
    on_shutdown = shutdown


if __name__ == "__main__":
    from arq import run_worker
    run_worker(WorkerSettings)

