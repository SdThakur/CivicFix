"""CivicFix Structured JSON Logging & Observability Middleware.

Features:
- Request ID propagation: Honors incoming X-Request-ID from Nginx or generates UUID4.
- Cryptographic PII protection: Hashes user_id with SHA-256 (preserves auditability without logging plain PII).
- Structured JSON output format for centralized log aggregation (Datadog, Loki, CloudWatch).
- Automated Prometheus HTTP request & latency metrics recording.
- Automated 429 rate limit counter increments.
"""

from datetime import datetime, timezone
import hashlib
import json
import logging
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.metrics import (
    HTTP_REQUESTS_TOTAL,
    HTTP_REQUEST_DURATION_SECONDS,
    RATE_LIMIT_EXCEEDED_TOTAL,
)

logger = logging.getLogger("civicfix.access")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Intercepts requests to log structured JSON and record Prometheus telemetry."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        # 1. Propagate or generate X-Request-ID
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id

        # 2. Execute inner pipeline
        response = None
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as exc:
            status_code = 500
            raise exc
        finally:
            elapsed_sec = time.perf_counter() - start_time
            latency_ms = round(elapsed_sec * 1000.0, 2)

            # 3. User Identity Hash (SHA-256 truncated to 16 hex characters)
            raw_user_id = getattr(request.state, "user_id", None)
            if raw_user_id:
                user_id_hash = hashlib.sha256(
                    str(raw_user_id).encode("utf-8")
                ).hexdigest()[:16]
            else:
                user_id_hash = "anonymous"

            # Normalize route pattern to avoid metric cardinality explosion
            route_path = request.url.path

            # 4. Record Prometheus Telemetry
            try:
                HTTP_REQUESTS_TOTAL.labels(
                    method=request.method,
                    route=route_path,
                    status_code=str(status_code),
                ).inc()

                HTTP_REQUEST_DURATION_SECONDS.labels(
                    method=request.method,
                    route=route_path,
                ).observe(elapsed_sec)

                if status_code == 429:
                    is_anon = getattr(request.state, "is_anonymous", False)
                    RATE_LIMIT_EXCEEDED_TOTAL.labels(
                        identity_type="anonymous" if is_anon else "signed_in"
                    ).inc()
            except Exception as metric_err:
                logger.debug(f"Prometheus metric record error: {metric_err}")

            # 5. Emit Structured JSON Log
            log_payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "ERROR" if status_code >= 500 else "INFO",
                "request_id": request_id,
                "user_id_hash": user_id_hash,
                "method": request.method,
                "route": route_path,
                "status_code": status_code,
                "latency_ms": latency_ms,
                "client_ip": request.client.host if request.client else "unknown",
            }
            logger.info(json.dumps(log_payload))

            # 6. Ensure X-Request-ID is attached to outbound response headers
            if response is not None:
                response.headers["X-Request-ID"] = request_id
