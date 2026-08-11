"""API router for GIS and Spatial Queries."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user
from app.models.user import User, UserRole
from app.services.spatial_query_service import SpatialQueryService

router = APIRouter(prefix="/gis", tags=["GIS & Spatial"])


def verify_staff_access(current_user: Optional[User]) -> None:
    if not current_user or current_user.role not in [UserRole.STAFF, UserRole.MANAGER, UserRole.SUPERVISOR, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not enough permissions")


@router.get("/spatial-summary", response_model=Dict[str, Any])
async def get_spatial_summary(
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Publicly accessible spatial summary."""
    return await SpatialQueryService.get_spatial_summary(db)


@router.get("/hotspot-segments", response_model=List[Dict[str, Any]])
async def get_hotspot_segments(
    min_incidents: int = Query(10),
    days: int = Query(90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    verify_staff_access(current_user)
    segments = await SpatialQueryService.get_hotspot_segments(db, min_incidents, days)
    return [{"id": s.id, "name": getattr(s, 'name', 'Unknown'), "risk_score": getattr(s, 'risk_score', 0)} for s in segments]


@router.get("/issues-in-zone/{zone_id}", response_model=List[Dict[str, Any]])
async def get_issues_in_zone(
    zone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    verify_staff_access(current_user)
    issues = await SpatialQueryService.get_issues_in_maintenance_zone(db, zone_id)
    return [{"id": i.id, "title": getattr(i, 'title', '')} for i in issues]


@router.get("/work-orders-near-crew", response_model=List[Dict[str, Any]])
async def get_work_orders_near_crew(
    crew_lat: float,
    crew_lng: float,
    radius_miles: float = Query(2.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    verify_staff_access(current_user)
    wos = await SpatialQueryService.get_open_work_orders_near_crew(db, crew_lat, crew_lng, radius_miles)
    return [{"id": wo.id, "title": getattr(wo, 'title', ''), "status": wo.status.value if hasattr(wo.status, 'value') else str(wo.status)} for wo in wos]


@router.get("/assets-near", response_model=List[Dict[str, Any]])
async def get_assets_near(
    lat: float,
    lng: float,
    radius_m: float = Query(200.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    verify_staff_access(current_user)
    # Using critical infra locations as a proxy for the query parameter
    infra_locations = [{"lat": lat, "lng": lng}]
    assets = await SpatialQueryService.get_assets_near_critical_infrastructure(db, infra_locations, radius_m)
    return [{"id": a.id, "type": getattr(a, 'asset_type', 'Unknown'), "condition": getattr(a, 'condition_score', None)} for a in assets]
