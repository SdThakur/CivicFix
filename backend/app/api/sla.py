"""SLA API Router."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.models.sla import SLARule, SLAEscalationLog
from app.schemas.sla import SLARuleRead, SLARuleCreate, SLAEscalationLogRead, SLAStatusResponse
from app.services.sla_service import SLAService
from app.models.report import Report

router = APIRouter(prefix="/sla", tags=["SLA"])

@router.get("/rules", response_model=List[SLARuleRead])
async def list_rules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN]))
) -> List[SLARuleRead]:
    """List SLA rules."""
    result = await db.execute(select(SLARule))
    rules = list(result.scalars().all())
    return [SLARuleRead.model_validate(r) for r in rules]

@router.post("/rules", response_model=SLARuleRead, status_code=status.HTTP_201_CREATED)
async def create_rule(
    rule_in: SLARuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
) -> SLARuleRead:
    """Create a new SLA rule."""
    rule = SLARule(**rule_in.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return SLARuleRead.model_validate(rule)

@router.get("/dashboard", response_model=Dict[str, int])
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN]))
) -> Dict[str, int]:
    """Get SLA dashboard metrics."""
    return await SLAService.get_sla_dashboard(db)

@router.get("/breached", response_model=List[SLAStatusResponse])
async def list_breached(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN]))
) -> List[SLAStatusResponse]:
    """List service requests with breached SLA."""
    # Mock implementation
    return []

@router.post("/check-escalations", response_model=List[SLAEscalationLogRead])
async def check_escalations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
) -> List[SLAEscalationLogRead]:
    """Trigger SLA escalation checks."""
    logs = await SLAService.check_and_escalate(db)
    return [SLAEscalationLogRead.model_validate(lg) for lg in logs]
