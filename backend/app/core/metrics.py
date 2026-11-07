"""CivicFix Prometheus Metrics Registry.

Defines operational telemetry metrics:
- HTTP request rates, status codes, and latency distributions
- Rate limiting 429 rejection counts
- ARQ worker queue depth and job latency
- Gemini AI inference latency and concurrency slot wait times
- Edge / Redis cache hit ratios
- Circuit breaker state gauges
"""

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    REGISTRY,
    generate_latest,
)

# Shared or custom registry
registry = REGISTRY

# ─── 1. HTTP API Request Metrics ─────────────────────────────────────────────
HTTP_REQUESTS_TOTAL = Counter(
    "civicfix_http_requests_total",
    "Total count of HTTP requests handled by CivicFix API",
    ["method", "route", "status_code"],
    registry=registry,
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "civicfix_http_request_duration_seconds",
    "HTTP request execution latency in seconds",
    ["method", "route"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0],
    registry=registry,
)

# ─── 2. Rate Limiting 429 Metrics ───────────────────────────────────────────
RATE_LIMIT_EXCEEDED_TOTAL = Counter(
    "civicfix_rate_limit_exceeded_total",
    "Total number of 429 Too Many Requests rate limit rejections",
    ["identity_type"],  # 'signed_in' or 'anonymous'
    registry=registry,
)

# ─── 3. Durable Queue Metrics ───────────────────────────────────────────────
QUEUE_DEPTH = Gauge(
    "civicfix_queue_depth",
    "Current number of reports pending or queued in durable queue",
    registry=registry,
)

QUEUE_JOB_LATENCY_SECONDS = Histogram(
    "civicfix_queue_job_latency_seconds",
    "Total queue-to-processed background triage job duration in seconds",
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 60.0],
    registry=registry,
)

# ─── 4. Gemini AI & Concurrency Slot Metrics ─────────────────────────────────
GEMINI_LATENCY_SECONDS = Histogram(
    "civicfix_gemini_latency_seconds",
    "Duration of outbound Gemini Vision AI calls in seconds",
    buckets=[0.2, 0.5, 1.0, 2.0, 4.0, 8.0, 15.0],
    registry=registry,
)

GEMINI_WAIT_SECONDS = Histogram(
    "civicfix_gemini_wait_seconds",
    "Time spent acquiring global Gemini concurrency slot in seconds",
    buckets=[0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    registry=registry,
)

GEMINI_BUDGET_USAGE_RATIO = Gauge(
    "civicfix_gemini_budget_usage_ratio",
    "Current fraction of daily Gemini AI budget consumed (0.0 to 1.0)",
    registry=registry,
)

# ─── 5. Cache & Edge Micro-Cache Metrics ────────────────────────────────────
CACHE_REQUESTS_TOTAL = Counter(
    "civicfix_cache_requests_total",
    "Total count of cache lookups categorized by outcome",
    ["status"],  # 'hit', 'miss', 'bypass'
    registry=registry,
)

# ─── 6. Resilience & Circuit Breaker Metrics ─────────────────────────────────
CIRCUIT_BREAKER_STATE = Gauge(
    "civicfix_circuit_breaker_state",
    "Circuit breaker state: 0=CLOSED (healthy), 1=HALF_OPEN (probing), 2=OPEN (tripped)",
    ["service"],
    registry=registry,
)


def get_prometheus_metrics() -> bytes:
    """Serialize all registered Prometheus metrics to Prometheus text exposition format."""
    return generate_latest(registry)
