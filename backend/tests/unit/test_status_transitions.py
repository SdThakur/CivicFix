"""Unit tests for Status Transition Validation."""

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.report import Report, ReportCategory, ReportStatus, PriorityLevel
from app.models.issue import Issue, IssueStatus
from app.models.work_order import WorkOrder, WorkOrderStatus
from app.models.user import User
from app.services.report_service import report_service
from app.services.issue_service import issue_service
from app.services.work_order_service import work_order_service


@pytest.mark.asyncio
async def test_valid_report_status_transition(
    db_session: AsyncSession, citizen_user: User
):
    """Verify valid report status progression SUBMITTED -> UNDER_REVIEW -> APPROVED."""
    report = Report(
        tracking_number="REP-TRANS-001",
        title="Test Pothole",
        category=ReportCategory.POTHOLE,
        description="Test description",
        status=ReportStatus.SUBMITTED,
        priority=PriorityLevel.MEDIUM,
        user_id=citizen_user.id,
        latitude=37.7749,
        longitude=-122.4194,
        address="100 Main St",
        neighborhood="Downtown",
    )
    db_session.add(report)
    await db_session.flush()

    # SUBMITTED -> UNDER_REVIEW
    updated = await report_service.update_report_status(
        db=db_session, report_id=report.id, new_status=ReportStatus.UNDER_REVIEW
    )
    assert updated.status == ReportStatus.UNDER_REVIEW

    # UNDER_REVIEW -> APPROVED
    updated = await report_service.update_report_status(
        db=db_session, report_id=report.id, new_status=ReportStatus.APPROVED
    )
    assert updated.status == ReportStatus.APPROVED


@pytest.mark.asyncio
async def test_invalid_report_status_transition(
    db_session: AsyncSession, citizen_user: User
):
    """Verify exception is raised for invalid transition (e.g. REJECTED -> RESOLVED)."""
    report = Report(
        tracking_number="REP-TRANS-002",
        title="Rejected Pothole",
        category=ReportCategory.POTHOLE,
        description="Test description",
        status=ReportStatus.REJECTED,
        priority=PriorityLevel.MEDIUM,
        user_id=citizen_user.id,
        latitude=37.7749,
        longitude=-122.4194,
        address="100 Main St",
        neighborhood="Downtown",
    )
    db_session.add(report)
    await db_session.flush()

    with pytest.raises(HTTPException) as exc_info:
        await report_service.update_report_status(
            db=db_session, report_id=report.id, new_status=ReportStatus.RESOLVED
        )

    assert exc_info.value.status_code == 400
    assert "Invalid status transition" in exc_info.value.detail


@pytest.mark.asyncio
async def test_valid_issue_status_transition(
    db_session: AsyncSession, sample_department
):
    """Verify Issue state progression OPEN -> IN_PROGRESS -> RESOLVED."""
    issue = Issue(
        issue_code="ISS-TRANS-001",
        title="Main Street Water Leak",
        category=ReportCategory.WATER_LEAK,
        description="Leaking water main",
        status=IssueStatus.OPEN,
        priority=PriorityLevel.HIGH,
        department_id=sample_department.id,
        latitude=37.7749,
        longitude=-122.4194,
        address="100 Main St",
        neighborhood="Downtown",
    )
    db_session.add(issue)
    await db_session.flush()

    # OPEN -> IN_PROGRESS
    updated = await issue_service.update_issue_status(
        db=db_session, issue_id=issue.id, new_status=IssueStatus.IN_PROGRESS
    )
    assert updated.status == IssueStatus.IN_PROGRESS

    # IN_PROGRESS -> RESOLVED
    updated = await issue_service.update_issue_status(
        db=db_session, issue_id=issue.id, new_status=IssueStatus.RESOLVED
    )
    assert updated.status == IssueStatus.RESOLVED
