"""Report repository handling data access layer for citizen reports."""

import math
from typing import List, Optional, Union, Dict, Any, Tuple
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.report import Report, ReportCategory, ReportStatus, PriorityLevel
from app.schemas.report import ReportCreate, ReportUpdate, ReportFilter


class ReportRepository:
    """Async repository for Report database operations."""

    async def get_by_id(self, db: AsyncSession, report_id: int) -> Optional[Report]:
        """Fetch report by primary key ID."""
        result = await db.execute(select(Report).where(Report.id == report_id))
        return result.scalars().first()

    async def get_by_tracking_number(
        self, db: AsyncSession, tracking_number: str
    ) -> Optional[Report]:
        """Fetch report by unique tracking number string."""
        result = await db.execute(
            select(Report).where(Report.tracking_number == tracking_number)
        )
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, filters: Optional[ReportFilter] = None
    ) -> Tuple[List[Report], int]:
        """Get paginated, filtered list of reports along with total count."""
        query = select(Report)
        count_query = select(func.count(Report.id))

        if filters:
            conditions = []
            if filters.status:
                conditions.append(Report.status == filters.status)
            if filters.category:
                conditions.append(Report.category == filters.category)
            if filters.priority:
                conditions.append(Report.priority == filters.priority)
            if filters.neighborhood:
                conditions.append(
                    func.lower(Report.neighborhood) == filters.neighborhood.lower()
                )
            if filters.user_id is not None:
                conditions.append(Report.user_id == filters.user_id)
            if filters.is_duplicate is not None:
                conditions.append(Report.is_duplicate == filters.is_duplicate)

            if conditions:
                query = query.where(and_(*conditions))
                count_query = count_query.where(and_(*conditions))

        # Count total matches
        count_res = await db.execute(count_query)
        total = count_res.scalar() or 0

        # Pagination & sorting
        skip = filters.skip if filters else 0
        limit = filters.limit if filters else 50
        query = query.order_by(Report.created_at.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        reports = list(result.scalars().all())
        return reports, total

    async def get_nearby(
        self,
        db: AsyncSession,
        latitude: float,
        longitude: float,
        radius_km: float = 2.0,
        category: Optional[ReportCategory] = None,
        limit: int = 50,
    ) -> List[Report]:
        """Geospatial bounding-box / distance query to find reports near a coordinate."""
        # Convert radius in km to approximate lat/lon degrees (1 deg lat ~ 111km)
        lat_delta = radius_km / 111.0
        lon_delta = radius_km / (111.0 * max(0.1, math.cos(math.radians(latitude))))

        query = select(Report).where(
            and_(
                Report.latitude >= latitude - lat_delta,
                Report.latitude <= latitude + lat_delta,
                Report.longitude >= longitude - lon_delta,
                Report.longitude <= longitude + lon_delta,
            )
        )

        if category:
            query = query.where(Report.category == category)

        query = query.limit(limit)
        result = await db.execute(query)
        candidates = list(result.scalars().all())

        # Exact Haversine distance filtering
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371.0  # Earth radius in kilometers
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

        nearby_reports = [
            rep
            for rep in candidates
            if haversine(latitude, longitude, rep.latitude, rep.longitude) <= radius_km
        ]
        return nearby_reports

    async def create(
        self,
        db: AsyncSession,
        obj_in: ReportCreate,
        tracking_number: str,
        user_id: int,
        priority: PriorityLevel = PriorityLevel.MEDIUM,
        ai_score: float = 0.0,
    ) -> Report:
        """Create a new citizen report."""
        db_obj = Report(
            tracking_number=tracking_number,
            title=obj_in.title,
            category=obj_in.category,
            description=obj_in.description,
            status=ReportStatus.SUBMITTED,
            priority=priority,
            user_id=user_id,
            latitude=obj_in.latitude,
            longitude=obj_in.longitude,
            address=obj_in.address,
            neighborhood=obj_in.neighborhood,
            image_urls=obj_in.image_urls,
            ai_score=ai_score,
        )
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        db_obj: Report,
        obj_in: Union[ReportUpdate, Dict[str, Any]],
    ) -> Report:
        """Update report fields."""
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

    async def count_by_status(self, db: AsyncSession) -> Dict[str, int]:
        """Aggregate report counts grouped by status."""
        query = select(Report.status, func.count(Report.id)).group_by(Report.status)
        result = await db.execute(query)
        return {str(status.value): count for status, count in result.all()}

    async def count_by_category(self, db: AsyncSession) -> Dict[str, int]:
        """Aggregate report counts grouped by category."""
        query = select(Report.category, func.count(Report.id)).group_by(Report.category)
        result = await db.execute(query)
        return {str(cat.value): count for cat, count in result.all()}


report_repo = ReportRepository()
