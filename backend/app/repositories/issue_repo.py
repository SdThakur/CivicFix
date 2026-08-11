"""Issue repository handling data access layer for aggregated issues."""

import math
from typing import List, Optional, Union, Dict, Any, Tuple
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.issue import Issue, IssueStatus
from app.models.report import PriorityLevel, ReportCategory
from app.schemas.issue import IssueCreate, IssueUpdate


class IssueRepository:
    """Async repository for Issue database operations."""

    async def get_by_id(self, db: AsyncSession, issue_id: int) -> Optional[Issue]:
        """Fetch issue by ID."""
        result = await db.execute(select(Issue).where(Issue.id == issue_id))
        return result.scalars().first()

    async def get_by_code(self, db: AsyncSession, issue_code: str) -> Optional[Issue]:
        """Fetch issue by issue code string."""
        result = await db.execute(select(Issue).where(Issue.issue_code == issue_code))
        return result.scalars().first()

    async def get_multi(
        self,
        db: AsyncSession,
        status: Optional[IssueStatus] = None,
        category: Optional[ReportCategory] = None,
        priority: Optional[PriorityLevel] = None,
        department_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Issue], int]:
        """Get paginated issues with filtering and total count."""
        query = select(Issue)
        count_query = select(func.count(Issue.id))
        conditions = []

        if status:
            conditions.append(Issue.status == status)
        if category:
            conditions.append(Issue.category == category)
        if priority:
            conditions.append(Issue.priority == priority)
        if department_id:
            conditions.append(Issue.department_id == department_id)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        count_res = await db.execute(count_query)
        total = count_res.scalar() or 0

        query = query.order_by(Issue.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        issues = list(result.scalars().all())
        return issues, total

    async def find_matching_issue_near(
        self,
        db: AsyncSession,
        latitude: float,
        longitude: float,
        category: ReportCategory,
        max_dist_km: float = 0.1,  # ~100 meters
    ) -> Optional[Issue]:
        """Find an existing active issue of same category within spatial threshold."""
        lat_delta = max_dist_km / 111.0
        lon_delta = max_dist_km / (111.0 * max(0.1, math.cos(math.radians(latitude))))

        query = select(Issue).where(
            and_(
                Issue.category == category,
                Issue.status.in_([IssueStatus.OPEN, IssueStatus.IN_PROGRESS]),
                Issue.latitude >= latitude - lat_delta,
                Issue.latitude <= latitude + lat_delta,
                Issue.longitude >= longitude - lon_delta,
                Issue.longitude <= longitude + lon_delta,
            )
        )
        result = await db.execute(query)
        candidates = list(result.scalars().all())

        def haversine(lat1, lon1, lat2, lon2):
            R = 6371.0
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = (
                math.sin(dlat / 2) ** 2
                + math.cos(math.radians(lat1))
                * math.cos(math.radians(lat2))
                * math.sin(dlon / 2) ** 2
            )
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            return R * c

        for candidate in candidates:
            if (
                haversine(latitude, longitude, candidate.latitude, candidate.longitude)
                <= max_dist_km
            ):
                return candidate

        return None

    async def create(
        self,
        db: AsyncSession,
        obj_in: IssueCreate,
        issue_code: str,
        department_id: Optional[int] = None,
    ) -> Issue:
        """Create a new aggregated Issue."""
        db_obj = Issue(
            issue_code=issue_code,
            title=obj_in.title,
            category=obj_in.category,
            description=obj_in.description,
            status=IssueStatus.OPEN,
            priority=obj_in.priority or PriorityLevel.MEDIUM,
            department_id=department_id or obj_in.department_id,
            assigned_to_id=obj_in.assigned_to_id,
            latitude=obj_in.latitude,
            longitude=obj_in.longitude,
            address=obj_in.address,
            neighborhood=obj_in.neighborhood,
            estimated_cost=obj_in.estimated_cost or 0.0,
            total_reports_count=1,
            score=50.0,
        )
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        db_obj: Issue,
        obj_in: Union[IssueUpdate, Dict[str, Any]],
    ) -> Issue:
        """Update existing issue."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field) and value is not None:
                setattr(db_obj, field, value)

        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj


issue_repo = IssueRepository()
