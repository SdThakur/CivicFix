"""Analytics API Router."""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.analytics import (
    DashboardStats,
    ResolutionTimeStats,
    HeatmapPoint,
)
from app.services.analytics_service import analytics_service
from app.models.user import UserRole
from app.api.deps import require_roles

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
) -> DashboardStats:
    """Retrieve executive dashboard metrics."""
    return await analytics_service.get_dashboard_stats(db=db)


@router.get("/resolution-times", response_model=List[ResolutionTimeStats])
async def get_resolution_time_stats(
    db: AsyncSession = Depends(get_db),
) -> List[ResolutionTimeStats]:
    """Retrieve average resolution time per category."""
    return await analytics_service.get_resolution_time_stats(db=db)


@router.get("/heatmap", response_model=List[HeatmapPoint])
async def get_heatmap_points(
    db: AsyncSession = Depends(get_db),
) -> List[HeatmapPoint]:
    """Retrieve spatial heatmap data points for geographic visualization."""
    return await analytics_service.get_heatmap_points(db=db)

@router.get("/department-performance", response_model=list[dict])
async def get_department_performance(
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.MANAGER, UserRole.ADMIN))
):
    """Retrieve department performance metrics."""
    return await analytics_service.get_department_performance(db=db)

@router.get("/crew-performance", response_model=list[dict])
async def get_crew_performance(
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.MANAGER, UserRole.ADMIN))
):
    """Retrieve crew performance metrics."""
    return await analytics_service.get_crew_performance(db=db)

@router.get("/infrastructure-performance", response_model=list[dict])
async def get_infrastructure_performance(
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_roles(UserRole.MANAGER, UserRole.ADMIN))
):
    """Retrieve infrastructure performance metrics."""
    return await analytics_service.get_infrastructure_performance(db=db)
