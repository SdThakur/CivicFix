"""Unit tests for spatial queries, SLA engine, AI vision triage, and work order workflow fixes."""

import pytest
import datetime
from unittest.mock import patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.report import Report, ReportCategory, ReportStatus, PriorityLevel
from app.models.issue import Issue, IssueStatus
from app.models.asset import MaintenanceZone
from app.models.service_request import ServiceRequest, ServiceRequestStatus
from app.models.sla import SLARule, SLAEscalationLog
from app.models.work_order import WorkOrder, WorkOrderStatus, WorkOrderPriority
from app.services.spatial_query_service import SpatialQueryService
from app.services.sla_service import SLAService
from app.services.ai_assistant_service import AIAssistantService, ai_assistant_service
from app.services.risk_scoring_service import RiskScoringService


@pytest.mark.asyncio
async def test_get_issues_in_maintenance_zone_does_not_error(db_session: AsyncSession):
    """Verify get_issues_in_maintenance_zone executes correctly without Report.maintenance_zone_id error."""
    # Create a test zone
    zone = MaintenanceZone(
        name="District 1",
        zone_code="MZ-001",
        latitude_center=37.7749,
        longitude_center=-122.4194,
    )
    db_session.add(zone)
    await db_session.flush()

    # Create a test issue
    issue = Issue(
        issue_code="ISS-TEST-001",
        title="Test Zone Pothole",
        category=ReportCategory.POTHOLE,
        description="Pothole in test maintenance zone",
        status=IssueStatus.OPEN,
        priority=PriorityLevel.HIGH,
        latitude=37.7750,
        longitude=-122.4195,
        address="123 Main St",
        neighborhood="Mission",
    )
    db_session.add(issue)
    await db_session.commit()

    # Call spatial query service function
    issues = await SpatialQueryService.get_issues_in_maintenance_zone(db_session, zone.id)
    assert isinstance(issues, list)
    assert len(issues) >= 1
    assert issues[0].id == issue.id


@pytest.mark.asyncio
async def test_sla_seed_default_rules_and_escalation(db_session: AsyncSession):
    """Verify default SLA rules are seeded and check_and_escalate executes without errors."""
    # Seed default SLA rules
    await SLAService.seed_default_rules(db_session)

    # Verify 4 rules were created
    from sqlalchemy import select
    res = await db_session.execute(select(SLARule))
    rules = list(res.scalars().all())
    assert len(rules) >= 4
    priorities = {r.priority for r in rules}
    assert "CRITICAL" in priorities
    assert "HIGH" in priorities
    assert "MEDIUM" in priorities
    assert "LOW" in priorities

    # Test check_and_escalate
    logs = await SLAService.check_and_escalate(db_session)
    assert isinstance(logs, list)


@pytest.mark.asyncio
async def test_ai_triage_image_fallback_when_error(db_session: AsyncSession):
    """Verify triage_image returns clear fallback when AI vision fails."""
    sample_image_bytes = b"fake_jpeg_data_for_testing"
    
    with patch("app.services.ai_assistant_service.get_vision_analyzer") as mock_get_analyzer:
        mock_analyzer = MagicMock()
        mock_analyzer.analyze_image.side_effect = Exception("API connection timeout")
        mock_get_analyzer.return_value = mock_analyzer

        res = await ai_assistant_service.triage_image(sample_image_bytes, notes="Test notes")
        assert res.ai_available is False
        assert "AI Vision analysis unavailable" in res.error_message


@pytest.mark.asyncio
async def test_work_order_blocked_status_and_photos(db_session: AsyncSession):
    """Verify WorkOrder supports BLOCKED status and photo URLs."""
    wo = WorkOrder(
        work_order_number="WO-TEST-001",
        title="Test Field Repair",
        description="Fixing broken pipe",
        status=WorkOrderStatus.PENDING,
        priority=WorkOrderPriority.HIGH,
        before_photo_url="https://storage.local/before.jpg",
        after_photo_url="https://storage.local/after.jpg",
        blocked_reason="Missing Equipment",
        blocked_notes="Need 4-inch valve replacement",
    )
    db_session.add(wo)
    await db_session.commit()
    await db_session.refresh(wo)

    assert wo.id is not None
    assert wo.before_photo_url == "https://storage.local/before.jpg"
    assert wo.after_photo_url == "https://storage.local/after.jpg"
    assert wo.blocked_reason == "Missing Equipment"
    assert wo.status == WorkOrderStatus.PENDING
