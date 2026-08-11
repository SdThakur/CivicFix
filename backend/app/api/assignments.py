"""API router for Intelligent Work Assignment."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User, UserRole
from app.schemas.work_order import WorkOrderResponse as WorkOrderRead
from app.services.assignment_service import AssignmentService

router = APIRouter(prefix="/assignments", tags=["Work Assignment"])


def verify_manager_access(current_user: User) -> None:
    if current_user.role not in [UserRole.MANAGER, UserRole.SUPERVISOR, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not enough permissions")


class ApplyRecommendationRequest(BaseModel):
    crew_id: int
    override_reason: Optional[str] = None


@router.get("/recommend/{work_order_id}", response_model=Dict[str, Any])
async def get_recommendation(
    work_order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    verify_manager_access(current_user)
    try:
        rec = await AssignmentService.get_recommendation_for_work_order(db, work_order_id)
        if not rec:
            raise HTTPException(status_code=404, detail="Could not generate recommendation")
        return {
            "recommended_crew_id": rec.recommended_crew_id,
            "recommended_crew_name": rec.recommended_crew_name,
            "total_score": rec.total_score,
            "distance_km": rec.distance_km,
            "reasons": rec.reasons,
            "score_breakdown": rec.score_breakdown,
            "alternative_crews": rec.alternative_crews,
            "can_meet_sla": rec.can_meet_sla,
            "estimated_response_minutes": rec.estimated_response_minutes
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/apply/{work_order_id}", response_model=WorkOrderRead)
async def apply_recommendation(
    work_order_id: int,
    data: ApplyRecommendationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    verify_manager_access(current_user)
    try:
        wo = await AssignmentService.apply_recommendation(
            db=db,
            work_order_id=work_order_id,
            crew_id=data.crew_id,
            assigned_by_id=current_user.id,
            override_reason=data.override_reason
        )
        return wo
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
