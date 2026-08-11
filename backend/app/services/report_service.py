"""Report Service handling submission, priority engine, duplicate detection, and routing."""

from datetime import datetime, timezone
import random
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.report import Report, ReportCategory, ReportStatus, PriorityLevel
from app.repositories.report_repo import report_repo
from app.schemas.report import (
    ReportCreate,
    ReportFilter,
    PriorityScoreBreakdown,
)
from app.services.notification_service import notification_service
from app.models.notification import NotificationType

# Priority category weight mapping
CATEGORY_PRIORITY_WEIGHTS = {
    ReportCategory.TRAFFIC_SIGNAL: 40.0,
    ReportCategory.WATER_LEAK: 35.0,
    ReportCategory.POTHOLE: 25.0,
    ReportCategory.STREETLIGHT: 20.0,
    ReportCategory.TRASH: 15.0,
    ReportCategory.PARK_DAMAGE: 15.0,
    ReportCategory.GRAFFITI: 10.0,
    ReportCategory.OTHER: 10.0,
}

# Category to Department Code mapping for automatic routing
CATEGORY_DEPARTMENT_MAP = {
    ReportCategory.POTHOLE: "DPW",
    ReportCategory.TRAFFIC_SIGNAL: "DPW",
    ReportCategory.STREETLIGHT: "DPW",
    ReportCategory.WATER_LEAK: "DWS",
    ReportCategory.GRAFFITI: "DPR",
    ReportCategory.PARK_DAMAGE: "DPR",
    ReportCategory.TRASH: "DSW",
    ReportCategory.OTHER: "GCS",
}


class ReportService:
    """Business logic engine for Citizen Infrastructure Reports."""

    def calculate_priority_score(
        self,
        category: ReportCategory,
        created_at: Optional[datetime] = None,
        upvotes: int = 0,
        duplicate_count: int = 0,
    ) -> PriorityScoreBreakdown:
        """Priority Engine: calculates 0-100 priority score and maps to PriorityLevel."""
        cat_weight = CATEGORY_PRIORITY_WEIGHTS.get(category, 10.0)

        # Age boost (0.5 pts per day, max 20)
        if created_at:
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            days_old = max(0.0, (now - created_at).total_seconds() / 86400.0)
            age_boost = min(20.0, days_old * 0.5)
        else:
            age_boost = 0.0

        # Upvote boost (2 pts per upvote, max 20)
        upvote_boost = min(20.0, upvotes * 2.0)

        # Duplicate cluster boost (5 pts per duplicate report, max 20)
        cluster_boost = min(20.0, duplicate_count * 5.0)

        final_score = cat_weight + age_boost + upvote_boost + cluster_boost

        if final_score >= 80.0:
            priority_level = PriorityLevel.URGENT
        elif final_score >= 60.0:
            priority_level = PriorityLevel.HIGH
        elif final_score >= 30.0:
            priority_level = PriorityLevel.MEDIUM
        else:
            priority_level = PriorityLevel.LOW

        return PriorityScoreBreakdown(
            category_weight=cat_weight,
            age_boost=round(age_boost, 2),
            upvote_boost=round(upvote_boost, 2),
            duplicate_cluster_boost=round(cluster_boost, 2),
            final_score=round(final_score, 2),
            calculated_priority=priority_level,
        )

    def route_department_code(self, category: ReportCategory) -> str:
        """Get target department code by report category."""
        return CATEGORY_DEPARTMENT_MAP.get(category, "GCS")

    async def find_duplicate_report(
        self,
        db: AsyncSession,
        latitude: float,
        longitude: float,
        category: ReportCategory,
        max_dist_km: float = 0.1,  # 100 meters
    ) -> Optional[Report]:
        """Duplicate Detection Engine: search for nearby matching reports within spatial radius."""
        nearby = await report_repo.get_nearby(
            db=db,
            latitude=latitude,
            longitude=longitude,
            radius_km=max_dist_km,
            category=category,
            limit=10,
        )
        for rep in nearby:
            if not rep.is_duplicate and rep.status != ReportStatus.REJECTED:
                return rep
        return None

    async def submit_report(
        self, db: AsyncSession, report_in: ReportCreate, user_id: int
    ) -> Report:
        """Submit a new report with priority calculation, duplicate detection, and notification."""
        tracking_num = f"REP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

        priority_breakdown = self.calculate_priority_score(
            category=report_in.category
        )

        report = await report_repo.create(
            db=db,
            obj_in=report_in,
            tracking_number=tracking_num,
            user_id=user_id,
            priority=priority_breakdown.calculated_priority,
            ai_score=priority_breakdown.final_score,
        )

        duplicate_candidate = await self.find_duplicate_report(
            db=db,
            latitude=report.latitude,
            longitude=report.longitude,
            category=report.category,
        )

        if duplicate_candidate and duplicate_candidate.id != report.id:
            report.is_duplicate = True
            report.duplicate_of_id = duplicate_candidate.id
            report.status = ReportStatus.DUPLICATE
            if duplicate_candidate.issue_id:
                report.issue_id = duplicate_candidate.issue_id
            await db.flush()

        await notification_service.send_notification(
            db=db,
            user_id=user_id,
            title="Report Submitted",
            message=f"Your report '{report.title}' has been submitted with tracking code {tracking_num}.",
            notification_type=NotificationType.REPORT_STATUS,
            reference_id=report.id,
            reference_type="report",
        )

        return report

    async def get_report(self, db: AsyncSession, report_id: int) -> Report:
        """Fetch report by ID or raise 404."""
        report = await report_repo.get_by_id(db, report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Report not found."
            )
        return report

    async def get_reports(
        self, db: AsyncSession, filters: ReportFilter
    ) -> Tuple[List[Report], int]:
        """Fetch paginated reports."""
        return await report_repo.get_multi(db, filters)

    async def update_report_status(
        self,
        db: AsyncSession,
        report_id: int,
        new_status: ReportStatus,
        issue_id: Optional[int] = None,
    ) -> Report:
        """Update report status enforcing valid status transitions and issue linking."""
        report = await self.get_report(db, report_id)

        valid_transitions = {
            ReportStatus.SUBMITTED: [
                ReportStatus.UNDER_REVIEW,
                ReportStatus.APPROVED,
                ReportStatus.REJECTED,
                ReportStatus.DUPLICATE,
            ],
            ReportStatus.UNDER_REVIEW: [
                ReportStatus.APPROVED,
                ReportStatus.REJECTED,
                ReportStatus.DUPLICATE,
            ],
            ReportStatus.APPROVED: [ReportStatus.IN_PROGRESS, ReportStatus.RESOLVED],
            ReportStatus.IN_PROGRESS: [ReportStatus.RESOLVED],
            ReportStatus.REJECTED: [],
            ReportStatus.DUPLICATE: [],
            ReportStatus.RESOLVED: [],
        }

        if (
            new_status != report.status
            and new_status not in valid_transitions.get(report.status, [])
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from {report.status.value} to {new_status.value}.",
            )

        report.status = new_status
        if issue_id is not None:
            report.issue_id = issue_id

        await db.flush()

        await notification_service.send_notification(
            db=db,
            user_id=report.user_id,
            title=f"Report Status Updated: {new_status.value}",
            message=f"Your report '{report.title}' ({report.tracking_number}) status is now {new_status.value}.",
            notification_type=NotificationType.REPORT_STATUS,
            reference_id=report.id,
            reference_type="report",
        )

        return report

    async def upvote_report(self, db: AsyncSession, report_id: int) -> Report:
        """Upvote report and recalculate its priority."""
        report = await self.get_report(db, report_id)
        report.upvotes += 1

        breakdown = self.calculate_priority_score(
            category=report.category,
            created_at=report.created_at,
            upvotes=report.upvotes,
        )
        report.priority = breakdown.calculated_priority
        report.ai_score = breakdown.final_score

        await db.flush()
        return report


report_service = ReportService()
