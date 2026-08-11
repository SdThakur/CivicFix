"""Unit tests for Duplicate Detection Engine."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.report import Report, ReportCategory, ReportStatus, PriorityLevel
from app.models.user import User
from app.repositories.report_repo import report_repo
from app.services.report_service import report_service


@pytest.mark.asyncio
async def test_duplicate_detection_within_radius(
    db_session: AsyncSession, citizen_user: User
):
    """Verify nearby report of same category is detected as duplicate."""
    base_lat, base_lon = 37.7749, -122.4194

    # 1. Create original report
    original = Report(
        tracking_number="REP-ORIG-001",
        title="Pothole on Main St",
        category=ReportCategory.POTHOLE,
        description="Deep pothole in middle lane",
        status=ReportStatus.SUBMITTED,
        priority=PriorityLevel.MEDIUM,
        user_id=citizen_user.id,
        latitude=base_lat,
        longitude=base_lon,
        address="100 Main St",
        neighborhood="Downtown",
    )
    db_session.add(original)
    await db_session.flush()

    # 2. Search candidate duplicate ~30 meters away
    dup_lat = base_lat + 0.0002
    dup_lon = base_lon + 0.0002

    dup_found = await report_service.find_duplicate_report(
        db=db_session,
        latitude=dup_lat,
        longitude=dup_lon,
        category=ReportCategory.POTHOLE,
        max_dist_km=0.1,  # 100m radius
    )

    assert dup_found is not None
    assert dup_found.id == original.id


@pytest.mark.asyncio
async def test_duplicate_detection_rejects_different_category(
    db_session: AsyncSession, citizen_user: User
):
    """Verify nearby report of DIFFERENT category is NOT flagged as duplicate."""
    base_lat, base_lon = 37.7749, -122.4194

    original = Report(
        tracking_number="REP-ORIG-002",
        title="Pothole on Main St",
        category=ReportCategory.POTHOLE,
        description="Deep pothole",
        status=ReportStatus.SUBMITTED,
        priority=PriorityLevel.MEDIUM,
        user_id=citizen_user.id,
        latitude=base_lat,
        longitude=base_lon,
        address="100 Main St",
        neighborhood="Downtown",
    )
    db_session.add(original)
    await db_session.flush()

    # Query same location but with WATER_LEAK category
    dup_found = await report_service.find_duplicate_report(
        db=db_session,
        latitude=base_lat,
        longitude=base_lon,
        category=ReportCategory.WATER_LEAK,
    )

    assert dup_found is None


@pytest.mark.asyncio
async def test_duplicate_detection_rejects_distant_location(
    db_session: AsyncSession, citizen_user: User
):
    """Verify report far away (> 500 meters) is NOT flagged as duplicate."""
    base_lat, base_lon = 37.7749, -122.4194

    original = Report(
        tracking_number="REP-ORIG-003",
        title="Pothole Downtown",
        category=ReportCategory.POTHOLE,
        description="Deep pothole",
        status=ReportStatus.SUBMITTED,
        priority=PriorityLevel.MEDIUM,
        user_id=citizen_user.id,
        latitude=base_lat,
        longitude=base_lon,
        address="100 Main St",
        neighborhood="Downtown",
    )
    db_session.add(original)
    await db_session.flush()

    # Query 2 kilometers away
    distant_lat = base_lat + 0.02
    dup_found = await report_service.find_duplicate_report(
        db=db_session,
        latitude=distant_lat,
        longitude=base_lon,
        category=ReportCategory.POTHOLE,
    )

    assert dup_found is None
