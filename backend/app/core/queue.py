"""CivicFix ARQ Durable Task Queue Producer.

Manages connection pool to QUEUE_REDIS_URL, idempotent report enqueueing,
and queue health monitoring.
"""

import logging
from typing import Optional
from arq.connections import ArqRedis, RedisSettings, create_pool
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_redis_settings(dsn: Optional[str] = None) -> RedisSettings:
    """Parse Redis connection string into ARQ RedisSettings."""
    url = dsn or settings.QUEUE_REDIS_URL
    rs = RedisSettings.from_dsn(url)
    rs.conn_retries = 1
    rs.conn_timeout = 1
    return rs


async def create_queue_pool(dsn: Optional[str] = None) -> Optional[ArqRedis]:
    """Create ARQ Redis connection pool with timeout protection."""
    url = dsn or settings.QUEUE_REDIS_URL
    try:
        redis_settings = get_redis_settings(url)
        pool = await create_pool(redis_settings)
        # Test ping
        await pool.ping()
        logger.info(f"ARQ Queue pool connected to Redis at {url}")
        return pool
    except Exception as e:
        logger.warning(f"Could not connect ARQ Queue pool to Redis at {url}: {e}")
        return None


async def enqueue_report(pool: Optional[ArqRedis], report_id: str) -> bool:
    """Enqueue a report for asynchronous background processing by ARQ worker.

    - Uses _job_id='report:{report_id}' for automatic deduplication.
    - If job already exists in queue, ARQ returns None (duplicate rejected).
    - If queue pool is disconnected or raises error, returns False without
      throwing, ensuring POST /reports returns 202 and row stays PENDING.
    """
    if pool is None:
        logger.warning(
            f"ARQ Queue pool unavailable when attempting to enqueue report {report_id}. "
            "Report will remain in PENDING state for sweeper recovery."
        )
        return False

    job_id = f"report:{report_id}"
    try:
        job = await pool.enqueue_job(
            "process_report_job",
            report_id,
            _job_id=job_id,
        )
        if job is None:
            logger.info(
                f"Job {job_id} already queued or running; duplicate enqueue rejected."
            )
            return False
        logger.info(
            f"Successfully enqueued report {report_id} to ARQ worker queue (job_id: {job_id})."
        )
        return True
    except Exception as e:
        logger.error(
            f"Failed to enqueue report {report_id} to ARQ queue: {e}. "
            "Report will remain in PENDING state for sweeper recovery."
        )
        return False
