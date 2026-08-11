"""Service Requests API routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.api.deps import get_db, get_current_active_user, require_roles
from app.models.user import User, UserRole
from app.models.service_request import ServiceRequestStatus
from app.schemas.service_request import (
    ServiceRequestRead,
    ServiceRequestCreate,
    ServiceRequestUpdate,
)
from app.services.service_request_service import ServiceRequestService


router = APIRouter(prefix="/service-requests", tags=["311 Service Requests"])


@router.get("/", response_model=List[ServiceRequestRead])
async def list_service_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[ServiceRequestStatus] = None,
    department_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STAFF, UserRole.MANAGER, UserRole.SUPERVISOR, UserRole.ADMIN)),
):
    """List service requests (staff only)."""
    return await ServiceRequestService.list_service_requests(
        db, skip=skip, limit=limit, status=status, department_id=department_id
    )


@router.post("/", response_model=ServiceRequestRead)
async def create_service_request(
    data: ServiceRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN)),
):
    """Create a new service request from an issue (staff only)."""
    try:
        reporter_id = data.reported_by_id or current_user.id
        return await ServiceRequestService.create_from_issue(
            db, issue_id=data.issue_id, reporter_id=reporter_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/sla/breached", response_model=List[ServiceRequestRead])
async def list_breached_sla(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.MANAGER, UserRole.ADMIN)),
):
    """List service requests that have breached SLAs (managers only)."""
    return await ServiceRequestService.get_overdue_sla(db)


@router.get("/issue/{issue_id}", response_model=Optional[ServiceRequestRead])
async def get_by_issue_id(
    issue_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get service request associated with an issue (public)."""
    sr = await ServiceRequestService.get_by_issue_id(db, issue_id)
    if not sr:
        raise HTTPException(status_code=404, detail="Service Request not found for issue")
    return sr


@router.get("/{sr_number}", response_model=ServiceRequestRead)
async def get_by_sr_number(
    sr_number: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a service request by SR number (public lookup)."""
    sr = await ServiceRequestService.get_by_sr_number(db, sr_number)
    if not sr:
        raise HTTPException(status_code=404, detail="Service Request not found")
    return sr


@router.patch("/{sr_id}", response_model=ServiceRequestRead)
async def update_service_request(
    sr_id: int,
    data: ServiceRequestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN)),
):
    """Update general fields on a service request (staff only)."""
    from sqlalchemy import select
    from app.models.service_request import ServiceRequest
    
    query = select(ServiceRequest).where(ServiceRequest.id == sr_id)
    result = await db.execute(query)
    sr = result.scalar_one_or_none()
    
    if not sr:
        raise HTTPException(status_code=404, detail="Service Request not found")
        
    update_data = data.model_dump(exclude_unset=True)
    
    if "status" in update_data:
        status_val = update_data.pop("status")
        await ServiceRequestService.update_status(
            db, sr_id, status_val, current_user.id, "Status updated via PATCH."
        )
        
    for key, value in update_data.items():
        setattr(sr, key, value)
        
    await db.commit()
    await db.refresh(sr)
    return sr


class StatusUpdateBody(BaseModel):
    status: ServiceRequestStatus
    notes: Optional[str] = None


@router.post("/{sr_id}/status", response_model=ServiceRequestRead)
async def update_status(
    sr_id: int,
    body: StatusUpdateBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN)),
):
    """Update status specifically, recording notes (staff only)."""
    try:
        return await ServiceRequestService.update_status(
            db, sr_id, body.status, current_user.id, body.notes
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
