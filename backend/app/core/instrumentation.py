"""Pipeline latency instrumentation for CivicFix AI processing steps.

Usage::

    with PipelineTimer("process_report") as timer:
        with timer.step("vision_analysis"):
            result = analyzer.analyze_image_sync(...)
        with timer.step("clip_embedding"):
            embedding = embedder.generate_embedding(...)

    report = timer.report()
    # report.total_ms       -> float, wall-clock ms for whole pipeline
    # report.steps          -> dict[str, float], ms per named step
    # report.within_sla     -> bool, True if total_ms < sla_threshold_ms
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, Generator, Optional

logger = logging.getLogger(__name__)

# Default SLA threshold that maps to the "sub-2-second" claim
DEFAULT_SLA_THRESHOLD_MS: float = 2000.0


@dataclass
class PipelineTimingReport:
    """Structured timing report produced after a pipeline run completes."""

    pipeline_name: str
    total_ms: float
    steps: Dict[str, float]
    sla_threshold_ms: float = DEFAULT_SLA_THRESHOLD_MS
    within_sla: bool = field(init=False)

    def __post_init__(self) -> None:
        self.within_sla = self.total_ms < self.sla_threshold_ms

    def as_dict(self) -> Dict[str, object]:
        """Return a JSON-serialisable representation."""
        return {
            "pipeline": self.pipeline_name,
            "total_ms": round(self.total_ms, 2),
            "steps_ms": {k: round(v, 2) for k, v in self.steps.items()},
            "sla_threshold_ms": self.sla_threshold_ms,
            "within_sla": self.within_sla,
        }

    def log_summary(self) -> None:
        """Emit a structured INFO log with per-step and total timings."""
        step_parts = ", ".join(
            f"{name}={ms:.1f}ms" for name, ms in self.steps.items()
        )
        sla_flag = "✓ WITHIN SLA" if self.within_sla else "✗ EXCEEDED SLA"
        logger.info(
            "[Pipeline: %s] total=%.1fms  %s  [%s]  steps: %s",
            self.pipeline_name,
            self.total_ms,
            sla_flag,
            f"threshold={self.sla_threshold_ms:.0f}ms",
            step_parts,
        )


class PipelineTimer:
    """Context-manager based wall-clock timer for multi-step AI pipelines.

    Attributes:
        pipeline_name: Human-readable label for the overall pipeline.
        sla_threshold_ms: SLA boundary in milliseconds (default 2 000 ms).

    Example::

        with PipelineTimer("triage_image") as timer:
            with timer.step("gemini_vision"):
                ...
            with timer.step("category_mapping"):
                ...
        report = timer.report()
    """

    def __init__(
        self,
        pipeline_name: str,
        sla_threshold_ms: float = DEFAULT_SLA_THRESHOLD_MS,
    ) -> None:
        self.pipeline_name = pipeline_name
        self.sla_threshold_ms = sla_threshold_ms
        self._steps: Dict[str, float] = {}
        self._pipeline_start: Optional[float] = None
        self._pipeline_end: Optional[float] = None

    # ── Context manager for the whole pipeline ─────────────────────────────

    def __enter__(self) -> "PipelineTimer":
        self._pipeline_start = time.perf_counter()
        return self

    def __exit__(self, *_: object) -> None:
        self._pipeline_end = time.perf_counter()
        self.report().log_summary()

    # ── Context manager for individual steps ───────────────────────────────

    @contextmanager
    def step(self, name: str) -> Generator[None, None, None]:
        """Time a named sub-step of the pipeline.

        Args:
            name: Short identifier for this step, e.g. ``"vision_analysis"``.
        """
        t0 = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            self._steps[name] = elapsed_ms

    # ── Report ──────────────────────────────────────────────────────────────

    def report(self) -> PipelineTimingReport:
        """Build and return a :class:`PipelineTimingReport` for this run.

        Can be called inside *or* after the ``with PipelineTimer(...)`` block.
        """
        if self._pipeline_start is None:
            raise RuntimeError("PipelineTimer was never entered as a context manager.")

        end = self._pipeline_end if self._pipeline_end is not None else time.perf_counter()
        total_ms = (end - self._pipeline_start) * 1000.0

        return PipelineTimingReport(
            pipeline_name=self.pipeline_name,
            total_ms=total_ms,
            steps=dict(self._steps),
            sla_threshold_ms=self.sla_threshold_ms,
        )
