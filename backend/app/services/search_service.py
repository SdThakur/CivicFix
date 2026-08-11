"""Search Service providing global full-text search across reports, issues, and work orders."""

from typing import Optional
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.report import Report
from app.models.issue import Issue
from app.models.work_order import WorkOrder
from app.schemas.search import SearchResult
from app.schemas.report import ReportResponse
from app.schemas.issue import IssueResponse
from app.schemas.work_order import WorkOrderResponse


class SearchService:
    """Business logic for cross-entity global searching."""

    async def search_all(
        self,
        db: AsyncSession,
        query_text: str,
        category: Optional[str] = None,
        neighborhood: Optional[str] = None,
        limit: int = 20,
    ) -> SearchResult:
        """Search across reports, issues, and work orders."""
        pattern = f"%{query_text.lower()}%"

        # Search Reports
        rep_query = select(Report).where(
            or_(
                func.lower(Report.title).like(pattern),
                func.lower(Report.description).like(pattern),
                func.lower(Report.address).like(pattern),
                func.lower(Report.tracking_number).like(pattern),
            )
        )
        if category:
            rep_query = rep_query.where(
                func.lower(Report.category) == category.lower()
            )
        if neighborhood:
            rep_query = rep_query.where(
                func.lower(Report.neighborhood) == neighborhood.lower()
            )
        rep_res = await db.execute(rep_query.limit(limit))
        reports = list(rep_res.scalars().all())

        # Search Issues
        issue_query = select(Issue).where(
            or_(
                func.lower(Issue.title).like(pattern),
                func.lower(Issue.description).like(pattern),
                func.lower(Issue.address).like(pattern),
                func.lower(Issue.issue_code).like(pattern),
            )
        )
        if category:
            issue_query = issue_query.where(
                func.lower(Issue.category) == category.lower()
            )
        if neighborhood:
            issue_query = issue_query.where(
                func.lower(Issue.neighborhood) == neighborhood.lower()
            )
        issue_res = await db.execute(issue_query.limit(limit))
        issues = list(issue_res.scalars().all())

        # Search Work Orders
        wo_query = select(WorkOrder).where(
            or_(
                func.lower(WorkOrder.title).like(pattern),
                func.lower(WorkOrder.description).like(pattern),
                func.lower(WorkOrder.work_order_number).like(pattern),
            )
        )
        wo_res = await db.execute(wo_query.limit(limit))
        work_orders = list(wo_res.scalars().all())

        total = len(reports) + len(issues) + len(work_orders)

        return SearchResult(
            query=query_text,
            reports=[ReportResponse.model_validate(r) for r in reports],
            issues=[IssueResponse.model_validate(i) for i in issues],
            work_orders=[WorkOrderResponse.model_validate(w) for w in work_orders],
            total_matches=total,
        )


search_service = SearchService()
