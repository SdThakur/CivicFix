"""Unit tests for Report Priority Engine calculation logic."""

from datetime import datetime, timedelta, timezone
from app.models.report import ReportCategory, PriorityLevel
from app.services.report_service import report_service


def test_category_base_weights():
    """Verify category base weight differentiation."""
    traffic = report_service.calculate_priority_score(ReportCategory.TRAFFIC_SIGNAL)
    graffiti = report_service.calculate_priority_score(ReportCategory.GRAFFITI)

    assert traffic.category_weight == 40.0
    assert graffiti.category_weight == 10.0
    assert traffic.final_score > graffiti.final_score


def test_upvote_boost_escalation():
    """Verify upvotes increase priority level score."""
    base = report_service.calculate_priority_score(ReportCategory.POTHOLE, upvotes=0)
    upvoted = report_service.calculate_priority_score(ReportCategory.POTHOLE, upvotes=15)

    assert upvoted.upvote_boost == 20.0  # Max cap 20
    assert upvoted.final_score == base.final_score + 20.0


def test_duplicate_cluster_boost():
    """Verify attached duplicate cluster size boosts urgency."""
    single = report_service.calculate_priority_score(ReportCategory.WATER_LEAK, duplicate_count=0)
    clustered = report_service.calculate_priority_score(ReportCategory.WATER_LEAK, duplicate_count=5)

    assert clustered.duplicate_cluster_boost == 20.0  # Max cap 20
    assert clustered.final_score > single.final_score


def test_age_boost_accumulation():
    """Verify aging report gains urgency score over time."""
    now = datetime.now(timezone.utc)
    fresh = report_service.calculate_priority_score(ReportCategory.PARK_DAMAGE, created_at=now)
    old = report_service.calculate_priority_score(ReportCategory.PARK_DAMAGE, created_at=now - timedelta(days=20))

    assert old.age_boost == 10.0
    assert old.final_score > fresh.final_score


def test_priority_level_mapping_thresholds():
    """Verify exact score mapping to Low, Medium, High, and Urgent enums."""
    urgent = report_service.calculate_priority_score(
        ReportCategory.TRAFFIC_SIGNAL, upvotes=10, duplicate_count=5
    )
    assert urgent.calculated_priority == PriorityLevel.URGENT
    assert urgent.final_score >= 80.0

    low = report_service.calculate_priority_score(ReportCategory.GRAFFITI)
    assert low.calculated_priority == PriorityLevel.LOW
    assert low.final_score < 30.0
