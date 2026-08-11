"""API router for Preventive Maintenance."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User, UserRole
from app.schemas.preventive_maintenance import (
    MaintenanceRecommendationRead,
    MaintenanceRecommendationApprove,
    MaintenanceRecommendationReject
)
from app.services.preventive_service import PreventiveMaintenanceService

router = APIRouter(prefix="/preventive-maintenance", tags=["Preventive Maintenance"])


def verify_manager_access(current_user: User) -> None:
    if current_user.role not in [UserRole.MANAGER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not enough permissions")


def verify_admin_access(current_user: User) -> None:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")


@router.get("/", response_model=List[MaintenanceRecommendationRead])
async def list_recommendations(
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    verify_manager_access(current_user)
    recs = await PreventiveMaintenanceService.list_recommendations(db, status=status, limit=limit)
    return recs


@router.get("/{rec_id}", response_model=MaintenanceRecommendationRead)
async def get_recommendation(
    rec_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    verify_manager_access(current_user)
    rec = await PreventiveMaintenanceService.get_by_id(db, rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return rec


@router.post("/scan", response_model=Dict[str, Any])
async def scan_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    verify_admin_access(current_user)
    recs = await PreventiveMaintenanceService.scan_for_recommendations(db)
    return {
        "created_count": len(recs),
        "recommendations": [{"id": r.id, "rec_number": r.rec_number} for r in recs]
    }


@router.post("/{rec_id}/approve", response_model=MaintenanceRecommendationRead)
async def approve_recommendation(
    rec_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    verify_manager_access(current_user)
    try:
        rec = await PreventiveMaintenanceService.approve_recommendation(db, rec_id, current_user.id)
        return rec
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{rec_id}/reject", response_model=MaintenanceRecommendationRead)
async def reject_recommendation(
    rec_id: int,
    data: MaintenanceRecommendationReject,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    verify_manager_access(current_user)
    try:
        rec = await PreventiveMaintenanceService.reject_recommendation(db, rec_id, data.rejection_reason)
        return rec
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
