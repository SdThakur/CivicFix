"""CivicFix Distributed Tracing with OpenTelemetry.

Provides:
- TracerProvider setup with OTLP exporter support (Datadog, Jaeger, Grafana Tempo).
- Helper trace span context managers for worker jobs, database queries, and Gemini calls.
- Safe no-op fallback when tracing endpoint is unconfigured.
"""

import logging
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

logger = logging.getLogger("civicfix.telemetry")

_tracer_initialized = False


def setup_telemetry(service_name: str = "civicfix-backend") -> trace.Tracer:
    """Initialize OpenTelemetry tracer provider with resource attributes."""
    global _tracer_initialized
    if not _tracer_initialized:
        resource = Resource.create(
            {
                "service.name": service_name,
                "service.version": "2.0.0",
                "deployment.environment": os.getenv("ENVIRONMENT", "production"),
            }
        )

        provider = TracerProvider(resource=resource)

        # Check for OTLP exporter endpoint
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        if otlp_endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                    OTLPSpanExporter,
                )

                exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
                provider.add_span_processor(BatchSpanProcessor(exporter))
                logger.info(
                    f"OpenTelemetry configured with OTLP exporter to {otlp_endpoint}"
                )
            except Exception as e:
                logger.warning(f"Could not load OTLP exporter: {e}")

        trace.set_tracer_provider(provider)
        _tracer_initialized = True

    return trace.get_tracer("civicfix.backend", "2.0.0")


tracer = setup_telemetry()
