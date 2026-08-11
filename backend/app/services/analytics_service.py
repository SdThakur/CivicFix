"""Analytics Service providing operational metrics and spatial heatmap data."""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.report import Report, ReportStatus, ReportCategory
from app.models.issue import Issue, IssueStatus
from app.models.work_order import WorkOrder, WorkOrderStatus
from app.schemas.analytics import (
    DashboardStats,
    CategoryCount,
    StatusCount,
    NeighborhoodStats,
    ResolutionTimeStats,
    HeatmapPoint,
)


class AnalyticsService:
    """Business logic for executive analytics and dashboard metrics."""

    async def get_dashboard_stats(self, db: AsyncSession) -> DashboardStats:
        """Aggregate high-level platform stats."""
        # 1. Total reports count
        total_reports_res = await db.execute(select(func.count(Report.id)))
        total_reports = total_reports_res.scalar() or 0

        # 2. Active issues (OPEN or IN_PROGRESS)
        active_issues_res = await db.execute(
            select(func.count(Issue.id)).where(
                Issue.status.in_([IssueStatus.OPEN, IssueStatus.IN_PROGRESS])
            )
        )
        active_issues = active_issues_res.scalar() or 0

        # 3. Pending work orders (PENDING or ASSIGNED)
        pending_wo_res = await db.execute(
            select(func.count(WorkOrder.id)).where(
                WorkOrder.status.in_([WorkOrderStatus.PENDING, WorkOrderStatus.ASSIGNED])
            )
        )
        pending_wo = pending_wo_res.scalar() or 0

        # 4. Resolved reports this month
        now = datetime.now(timezone.utc)
        first_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        resolved_month_res = await db.execute(
            select(func.count(Report.id)).where(
                and_(
                    Report.status == ReportStatus.RESOLVED,
                    Report.updated_at >= first_of_month,
                )
            )
        )
        resolved_month = resolved_month_res.scalar() or 0

        # 5. Status breakdown
        status_counts_res = await db.execute(
            select(Report.status, func.count(Report.id)).group_by(Report.status)
        )
        status_breakdown = [
            StatusCount(status=str(status.value), count=count)
            for status, count in status_counts_res.all()
        ]

        # 6. Category breakdown
        category_counts_res = await db.execute(
            select(Report.category, func.count(Report.id)).group_by(Report.category)
        )
        category_breakdown = []
        for cat, count in category_counts_res.all():
            pct = (count / total_reports * 100.0) if total_reports > 0 else 0.0
            category_breakdown.append(
                CategoryCount(
                    category=str(cat.value), count=count, percentage=round(pct, 2)
                )
            )

        # 7. Top Neighborhoods stats
        neighborhood_res = await db.execute(
            select(
                Report.neighborhood,
                func.count(Report.id).label("total"),
                func.sum(
                    case((Report.status == ReportStatus.RESOLVED, 1), else_=0)
                ).label("resolved"),
            )
            .group_by(Report.neighborhood)
            .order_by(func.count(Report.id).desc())
            .limit(5)
        )

        top_neighborhoods = [
            NeighborhoodStats(
                neighborhood=row[0],
                total_reports=row[1],
                resolved_reports=row[2] or 0,
                open_issues=max(0, row[1] - (row[2] or 0)),
            )
            for row in neighborhood_res.all()
        ]

        # 8. Compute real avg resolution time from resolved work orders
        wo_res = await db.execute(
            select(WorkOrder).where(
                and_(
                    WorkOrder.status == WorkOrderStatus.COMPLETED,
                    WorkOrder.actual_start.isnot(None),
                    WorkOrder.actual_end.isnot(None),
                )
            )
        )
        completed_wos = list(wo_res.scalars().all())

        if completed_wos:
            total_hours = sum(
                max(0.0, (wo.actual_end - wo.actual_start).total_seconds() / 3600.0)
                for wo in completed_wos
                if wo.actual_end and wo.actual_start
            )
            avg_resolution_days = round(total_hours / len(completed_wos) / 24.0, 1)
        else:
            # Fallback: compute from resolved reports (updated_at - created_at)
            resolved_res = await db.execute(
                select(Report).where(Report.status == ReportStatus.RESOLVED).limit(200)
            )
            resolved_reps = list(resolved_res.scalars().all())
            if resolved_reps:
                total_hours = sum(
                    max(0.0, (r.updated_at - r.created_at).total_seconds() / 3600.0)
                    for r in resolved_reps
                )
                avg_resolution_days = round(total_hours / len(resolved_reps) / 24.0, 1)
            else:
                avg_resolution_days = 0.0

        # 9. Resolution rate: resolved / total
        resolved_total_res = await db.execute(
            select(func.count(Report.id)).where(Report.status == ReportStatus.RESOLVED)
        )
        resolved_total = resolved_total_res.scalar() or 0
        resolution_rate_pct = round((resolved_total / total_reports * 100.0), 1) if total_reports > 0 else 0.0

        return DashboardStats(
            total_reports=total_reports,
            active_issues=active_issues,
            pending_work_orders=pending_wo,
            resolved_reports_this_month=resolved_month,
            resolved_reports_total=resolved_total,
            resolution_rate_pct=resolution_rate_pct,
            avg_resolution_time_days=avg_resolution_days,
            status_breakdown=status_breakdown,
            category_breakdown=category_breakdown,
            top_neighborhoods=top_neighborhoods,
        )

    async def get_resolution_time_stats(
        self, db: AsyncSession
    ) -> List[ResolutionTimeStats]:
        """Compute average resolution hours per category."""
        # Calculate time delta for resolved reports
        res = await db.execute(
            select(Report).where(Report.status == ReportStatus.RESOLVED)
        )
        resolved_reports = list(res.scalars().all())

        cat_times: Dict[str, List[float]] = {}
        for rep in resolved_reports:
            cat_str = str(rep.category.value)
            hours = (rep.updated_at - rep.created_at).total_seconds() / 3600.0
            cat_times.setdefault(cat_str, []).append(max(0.5, hours))

        result = []
        for cat_str, times in cat_times.items():
            avg_h = sum(times) / len(times)
            result.append(
                ResolutionTimeStats(
                    category=cat_str,
                    avg_resolution_hours=round(avg_h, 2),
                    total_resolved=len(times),
                )
            )

        if not result:
            # Default fallbacks if no resolved reports yet
            for cat in ReportCategory:
                result.append(
                    ResolutionTimeStats(
                        category=cat.value, avg_resolution_hours=24.0, total_resolved=0
                    )
                )

        return result

    async def get_heatmap_points(self, db: AsyncSession) -> List[HeatmapPoint]:
        """Retrieve spatial points for heatmap visualization."""
        res = await db.execute(select(Report).limit(1000))
        reports = list(res.scalars().all())

        heatmap = []
        for rep in reports:
            # Compute point weight (1.0 to 3.0 based on upvotes and priority)
            weight = 1.0 + (rep.upvotes * 0.2) + (rep.ai_score / 50.0)
            heatmap.append(
                HeatmapPoint(
                    latitude=rep.latitude,
                    longitude=rep.longitude,
                    weight=round(weight, 2),
                    category=str(rep.category.value),
                    status=str(rep.status.value),
                    title=rep.title,
                )
            )

        return heatmap

    async def get_department_performance(self, db: AsyncSession) -> list[dict]:
        """Department performance: backlog, completed, avg resolution time, SLA compliance."""
        # Query departments with their work order stats
        # Return: [{department_id, department_name, open_work_orders, completed_work_orders,
        #           avg_resolution_hours, sla_compliance_pct}]
        pass  # implement

    async def get_crew_performance(self, db: AsyncSession) -> list[dict]:
        """Crew workload and performance metrics."""
        # Query crews with work order assignments
        # Return: [{crew_id, crew_name, active_jobs, completed_jobs_30d, avg_completion_hours, utilization_pct}]
        pass  # implement

    async def get_infrastructure_performance(self, db: AsyncSession) -> list[dict]:
        """Most problematic road segments and recurring failures."""
        # Query road_segments ordered by incident_count_90d desc limit 20
        # Return: [{segment_id, segment_code, road_name, incident_count, risk_score, last_maintained_at}]
        pass  # implement


analytics_service = AnalyticsService()
