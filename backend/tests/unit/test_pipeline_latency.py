"""Pipeline latency instrumentation tests.

Validates that:
1. PipelineTimer correctly records wall-clock time for each step.
2. process_report_task returns a `timing_ms` payload with all expected step keys.
3. Total pipeline latency is below the 2-second SLA threshold (mock analyzer path).
4. triage_image() returns timing_ms in its response.

Run with:
    cd backend
    pytest tests/unit/test_pipeline_latency.py -v -s
"""

import time
import pytest
from app.core.instrumentation import PipelineTimer, PipelineTimingReport, DEFAULT_SLA_THRESHOLD_MS


# ─────────────────────────────────────────────────────────────────────────────
# PipelineTimer unit tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPipelineTimer:
    """Verify the PipelineTimer context manager and step recording."""

    def test_total_time_recorded(self):
        """total_ms must be positive and reflect actual elapsed wall time."""
        with PipelineTimer("test_pipeline") as timer:
            time.sleep(0.01)  # 10 ms sleep
        report = timer.report()
        assert report.total_ms >= 10.0, f"Expected >= 10ms, got {report.total_ms:.2f}ms"

    def test_step_times_recorded(self):
        """Each named step must appear in the report with a positive duration."""
        with PipelineTimer("test_pipeline") as timer:
            with timer.step("step_alpha"):
                time.sleep(0.005)
            with timer.step("step_beta"):
                time.sleep(0.005)

        report = timer.report()
        assert "step_alpha" in report.steps
        assert "step_beta" in report.steps
        assert report.steps["step_alpha"] >= 5.0
        assert report.steps["step_beta"] >= 5.0

    def test_within_sla_flag_true_for_fast_pipeline(self):
        """A fast pipeline (well under 2 s) must report within_sla=True."""
        with PipelineTimer("fast_pipeline", sla_threshold_ms=2000.0) as timer:
            with timer.step("noop"):
                pass
        report = timer.report()
        assert report.within_sla is True

    def test_within_sla_flag_false_for_slow_pipeline(self):
        """A pipeline that exceeds the custom threshold must report within_sla=False."""
        with PipelineTimer("slow_pipeline", sla_threshold_ms=1.0) as timer:
            with timer.step("slow_step"):
                time.sleep(0.01)  # 10 ms >> 1 ms threshold
        report = timer.report()
        assert report.within_sla is False

    def test_as_dict_serialisable(self):
        """as_dict() must return a JSON-compatible dict with required keys."""
        with PipelineTimer("dict_test") as timer:
            with timer.step("alpha"):
                pass
        d = timer.report().as_dict()
        assert d["pipeline"] == "dict_test"
        assert isinstance(d["total_ms"], float)
        assert isinstance(d["steps_ms"], dict)
        assert "alpha" in d["steps_ms"]
        assert isinstance(d["within_sla"], bool)

    def test_report_callable_inside_context(self):
        """report() called inside the context must return a valid partial report."""
        with PipelineTimer("partial_test") as timer:
            with timer.step("first"):
                pass
            interim = timer.report()
            assert interim.total_ms >= 0.0
            assert "first" in interim.steps


# ─────────────────────────────────────────────────────────────────────────────
# Full pipeline task latency test
# ─────────────────────────────────────────────────────────────────────────────

EXPECTED_PIPELINE_STEPS = {
    "vision_analysis",
    "clip_embedding",
    "reverse_geocoding",
    "duplicate_detection",
    "department_routing",
    "priority_scoring",
}


class TestProcessReportTaskLatency:
    """Verify process_report_task returns per-step timing and meets the SLA."""

    def test_timing_keys_present(self):
        """Result must include timing_ms with all 6 pipeline step keys."""
        from app.workers.tasks import process_report_task

        report_data = {
            "latitude": 37.7749,
            "longitude": -122.4194,
            "description": "Pothole near intersection",
            "image_bytes": b"mock_pothole_img",
        }
        result = process_report_task("test-report-001", report_data)

        assert "timing_ms" in result, "timing_ms missing from task result"
        timing = result["timing_ms"]
        assert "total_ms" in timing
        assert "steps_ms" in timing
        recorded_steps = set(timing["steps_ms"].keys())
        assert EXPECTED_PIPELINE_STEPS == recorded_steps, (
            f"Step mismatch.\n  Expected: {EXPECTED_PIPELINE_STEPS}\n  Got: {recorded_steps}"
        )

    def test_all_step_times_positive(self):
        """Every individual step must have a non-negative measured duration."""
        from app.workers.tasks import process_report_task

        report_data = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "description": "Broken streetlight",
            "image_bytes": b"mock_streetlight_img",
        }
        result = process_report_task("test-report-002", report_data)
        for step, ms in result["timing_ms"]["steps_ms"].items():
            assert ms >= 0.0, f"Step '{step}' has negative time: {ms}ms"

    def test_total_pipeline_within_2s_sla(self):
        """Mock-mode total pipeline must complete well under 2 000 ms SLA.

        With the mock vision analyzer and fallback CLIP embedder the pipeline
        should run in < 500 ms on any modern CPU.  The 2 000 ms limit
        specifically matches the public latency claim.
        """
        from app.workers.tasks import process_report_task

        report_data = {
            "latitude": 51.5074,
            "longitude": -0.1278,
            "description": "Blocked drain causing flooding",
            "image_bytes": b"mock_drain_img",
        }
        result = process_report_task("test-report-003", report_data)
        total_ms = result["timing_ms"]["total_ms"]

        print(f"\n{'─' * 52}")
        print(f"  {'Pipeline Latency Report':^50}")
        print(f"{'─' * 52}")
        for step, ms in result["timing_ms"]["steps_ms"].items():
            bar = "█" * max(1, int(ms / 5))
            print(f"  {step:<30} {ms:>8.2f} ms  {bar}")
        print(f"{'─' * 52}")
        print(f"  {'TOTAL':<30} {total_ms:>8.2f} ms")
        print(f"  {'SLA (sub-2s)':<30} {'✓ PASS' if total_ms < DEFAULT_SLA_THRESHOLD_MS else '✗ FAIL':>8}")
        print(f"{'─' * 52}\n")

        assert total_ms < DEFAULT_SLA_THRESHOLD_MS, (
            f"Pipeline took {total_ms:.1f}ms — exceeded {DEFAULT_SLA_THRESHOLD_MS:.0f}ms SLA"
        )


# ─────────────────────────────────────────────────────────────────────────────
# triage_image API path latency test
# ─────────────────────────────────────────────────────────────────────────────

class TestTriageImageLatency:
    """Verify the direct triage_image() path (no Celery) returns timing data."""

    @pytest.mark.asyncio
    async def test_triage_image_returns_timing_ms(self):
        """triage_image response must include timing_ms dict."""
        from app.services.ai_assistant_service import ai_assistant_service

        # Use 8-byte mock payload — triggers MockVisionAnalyzer fallback
        fake_image = b"FAKEJPEG"
        response = await ai_assistant_service.triage_image(fake_image, notes="test")

        assert response.timing_ms is not None, "timing_ms missing from triage_image response"
        assert "total_ms" in response.timing_ms
        assert "steps_ms" in response.timing_ms
        assert response.timing_ms["total_ms"] >= 0.0

    @pytest.mark.asyncio
    async def test_triage_image_gemini_step_timed(self):
        """The gemini_vision step must be individually recorded."""
        from app.services.ai_assistant_service import ai_assistant_service

        fake_image = b"FAKEJPEG"
        response = await ai_assistant_service.triage_image(fake_image)

        steps = response.timing_ms.get("steps_ms", {})
        assert "gemini_vision" in steps, f"gemini_vision step missing. Got: {list(steps.keys())}"
