"""Celery application instance configuration for background asynchronous task processing."""

import logging
import os

logger = logging.getLogger(__name__)

# Resolve Redis broker and result backend URLs from environment variables
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", os.getenv("REDIS_URL", "redis://localhost:6379/1"))

try:
    from celery import Celery
    HAS_CELERY = True

    # Initialize Celery app instance
    celery_app = Celery(
        "civicfix_workers",
        broker=CELERY_BROKER_URL,
        backend=CELERY_RESULT_BACKEND,
    )

    # Apply Celery configuration parameters
    celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=300,  # Hard timeout of 5 minutes
        task_soft_time_limit=240,  # Soft timeout of 4 minutes
        result_expires=86400,  # Results expire in 24 hours
        task_routes={
            "app.workers.tasks.process_report_task": {"queue": "reports"},
            "app.workers.tasks.run_hotspot_detection_task": {"queue": "analytics"},
            "app.workers.email_tasks.*": {"queue": "emails"},
        },
        imports=[
            "app.workers.tasks",
            "app.workers.email_tasks",
        ],
    )
    logger.info("Celery application initialized with broker: %s", CELERY_BROKER_URL)

except ImportError:
    HAS_CELERY = False
    logger.warning("Celery library not installed. Creating MockCelery App wrapper.")

    class DummyTaskResult:
        def __init__(self, task_id="mock-task-id"):
            self.id = task_id

    class MockCeleryConf(dict):
        def update(self, *args, **kwargs):
            super().update(*args, **kwargs)

    class MockCelery:
        def __init__(self, main=None, broker=None, backend=None):
            self.main = main
            self.conf = MockCeleryConf()

        def task(self, *args, **kwargs):
            is_bound = kwargs.get("bind", False)
            def decorator(func):
                def delay(*f_args, **f_kwargs):
                    logger.info("[MockCelery] Executing task synchronously '%s'", func.__name__)
                    if is_bound:
                        res = func(None, *f_args, **f_kwargs)
                    else:
                        res = func(*f_args, **f_kwargs)
                    return DummyTaskResult()
                func.delay = delay
                return func
            return decorator

        def start(self):
            pass

    celery_app = MockCelery("civicfix_workers", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

if __name__ == "__main__":
    if HAS_CELERY:
        celery_app.start()
