"""CivicFix Workers Module

Provides Celery application instance and asynchronous background tasks for
report processing, AI pipeline execution, geospatial analysis, and email notifications.
"""

from app.workers.celery_app import celery_app

__all__ = ["celery_app"]
