"""Issue Service handling issue lifecycle, status transitions, department assignment, and report linking."""

import random
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.issue import Issue, IssueStatus
from app.models.report import Report, ReportStatus, PriorityLevel, ReportCategory
from app.models.department import Department
from app.repositories.issue_repo import issue_repo
from app.repositories.report_repo import report_repo
from app.schemas.issue import IssueCreate, IssueUpdate
from app.services.notification_service import notification_service
from app.models.notification import NotificationType

# Category -> Department mapping helper
CATEGORY_DEPARTMENT_CODES = {
    ReportCategory.POTHOLE: "DPW",
    ReportCategory.TRAFFIC_SIGNAL: "DPW",
    ReportCategory.STREETLIGHT: "DPW",
    ReportCategory.WATER_LEAK: "DWS",
    ReportCategory.GRAFFITI: "DPR",
    ReportCategory.PARK_DAMAGE: "DPR",
    ReportCategory.TRASH: "DSW",
    ReportCategory.OTHER: "GCS",
}


class IssueService:
    """Business logic engine for aggregated Issues."""

    async def _resolve_department_id(
        self, db: AsyncSession, category: ReportCategory
    ) -> Optional[int]:
        """Find department ID by category routing code."""
        code = CATEGORY_DEPARTMENT_CODES.get(category, "GCS")
        result = await db.execute(select(Department).where(Department.code == code))
        dept = result.scalars().first()
        return dept.id if dept else None

    async def create_issue(
        self,
        db: AsyncSession,
        issue_in: IssueCreate,
        initial_report_id: Optional[int] = None,
    ) -> Issue:
        """Create a new Issue and link an initial report if provided."""
        # Generate issue code
        issue_code = f"ISS-{random.randint(10000, 99999)}"

        # Resolve department routing if not provided
        department_id = issue_in.department_id
        if not department_id:
            department_id = await self._resolve_department_id(db, issue_in.category)

        issue = await issue_repo.create(
            db=db,
            obj_in=issue_in,
            issue_code=issue_code,
            department_id=department_id,
        )

        # Link initial report if provided
        if initial_report_id:
            report = await report_repo.get_by_id(db, initial_report_id)
            if report:
                report.issue_id = issue.id
                report.status = ReportStatus.APPROVED
                await db.flush()

        return issue

    async def get_issue(self, db: AsyncSession, issue_id: int) -> Issue:
        """Get issue by ID or raise 404."""
        issue = await issue_repo.get_by_id(db, issue_id)
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found."
            )
        return issue

    async def get_issues(
        self,
        db: AsyncSession,
        status: Optional[IssueStatus] = None,
        category: Optional[ReportCategory] = None,
        priority: Optional[PriorityLevel] = None,
        department_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Issue], int]:
        """Get paginated issues."""
        return await issue_repo.get_multi(
            db,
            status=status,
            category=category,
            priority=priority,
            department_id=department_id,
            skip=skip,
            limit=limit,
        )

    async def update_issue(
        self, db: AsyncSession, issue_id: int, update_in: IssueUpdate
    ) -> Issue:
        """Update issue attributes and handle status transitions."""
        issue = await self.get_issue(db, issue_id)

        if update_in.status and update_in.status != issue.status:
            await self.update_issue_status(db, issue_id, update_in.status)
            update_in.status = None  # Already updated by handler

        updated_issue = await issue_repo.update(db=db, db_obj=issue, obj_in=update_in)
        return updated_issue

    async def update_issue_status(
        self, db: AsyncSession, issue_id: int, new_status: IssueStatus
    ) -> Issue:
        """Update issue status and cascade updates to associated reports and users."""
        issue = await self.get_issue(db, issue_id)

        # Valid transitions check
        valid_transitions = {
            IssueStatus.OPEN: [IssueStatus.IN_PROGRESS, IssueStatus.CLOSED],
            IssueStatus.IN_PROGRESS: [IssueStatus.RESOLVED, IssueStatus.OPEN],
            IssueStatus.RESOLVED: [IssueStatus.CLOSED, IssueStatus.IN_PROGRESS],
            IssueStatus.CLOSED: [IssueStatus.OPEN],
        }

        if (
            new_status != issue.status
            and new_status not in valid_transitions.get(issue.status, [])
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid issue status transition from {issue.status.value} to {new_status.value}.",
            )

        issue.status = new_status
        await db.flush()

        # Cascade status update to linked reports when RESOLVED
        if new_status == IssueStatus.RESOLVED:
            reports_res = await db.execute(
                select(Report).where(Report.issue_id == issue.id)
            )
            linked_reports = list(reports_res.scalars().all())
            for r in linked_reports:
                r.status = ReportStatus.RESOLVED
                await notification_service.send_notification(
                    db=db,
                    user_id=r.user_id,
                    title="Issue Resolved!",
                    message=f"The reported issue '{issue.title}' ({issue.issue_code}) has been resolved by municipal crew.",
                    notification_type=NotificationType.ISSUE_UPDATE,
                    reference_id=issue.id,
                    reference_type="issue",
                )

        return issue

    async def merge_report_into_issue(
        self, db: AsyncSession, issue_id: int, report_id: int
    ) -> Issue:
        """Link an additional report to an existing issue."""
        issue = await self.get_issue(db, issue_id)
        report = await report_repo.get_by_id(db, report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Report not found."
            )

        report.issue_id = issue.id
        report.status = ReportStatus.APPROVED
        issue.total_reports_count += 1

        # Elevate priority score based on cluster size
        issue.score = min(100.0, issue.score + 5.0)
        if issue.score >= 80.0:
            issue.priority = PriorityLevel.URGENT
        elif issue.score >= 60.0:
            issue.priority = PriorityLevel.HIGH

        await db.flush()
        return issue


issue_service = IssueService()
