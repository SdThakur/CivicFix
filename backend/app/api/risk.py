"""API router for Risk Scoring."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User, UserRole
from app.services.risk_scoring_service import RiskScoringService

router = APIRouter(prefix="/risk", tags=["Risk Scoring"])


def verify_staff_access(current_user: User) -> None:
    if current_user.role not in [UserRole.STAFF, UserRole.MANAGER, UserRole.SUPERVISOR, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
def verify_admin_access(current_user: User) -> None:
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Not enough permissions")


@router.get("/segments/high-risk", response_model=List[Dict[str, Any]])
async def get_high_risk_segments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    verify_staff_access(current_user)
    segments = await RiskScoringService.get_high_risk_segments(db)
    # Simply returning dict representation
    return [{"id": s.id, "name": getattr(s, 'name', 'Unknown'), "risk_score": s.risk_score} for s in segments]


@router.post("/segments/score-all", response_model=Dict[str, Any])
async def score_all_segments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    verify_admin_access(current_user)
    results = await RiskScoringService.score_all_segments(db)
    return {
        "status": "success",
        "processed_count": len(results),
        "results_sample": results[:5]
    }


@router.get("/segments/{segment_id}/score", response_model=Dict[str, Any])
async def get_segment_score(
    segment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    verify_staff_access(current_user)
    try:
        res = await RiskScoringService.score_road_segment(db, segment_id)
        return {
            "score": res.score,
            "label": res.label,
            "factors": res.factors,
            "explanation": res.explanation
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/segments/{segment_id}/recalculate", response_model=Dict[str, Any])
async def recalculate_segment_score(
    segment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    verify_admin_access(current_user)
    try:
        res = await RiskScoringService.score_road_segment(db, segment_id)
        return {
            "score": res.score,
            "label": res.label,
            "factors": res.factors,
            "explanation": res.explanation
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/assets/high-risk", response_model=List[Dict[str, Any]])
async def get_high_risk_assets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    verify_staff_access(current_user)
    assets = await RiskScoringService.get_high_risk_assets(db)
    return [{"id": a.id, "name": getattr(a, 'name', 'Unknown'), "risk_score": a.risk_score} for a in assets]
