"""Inspections API routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.schemas.inspection import (
    InspectionRead,
    InspectionCreate,
    InspectionUpdate,
)
from app.services.inspection_service import InspectionService

router = APIRouter(prefix="/inspections", tags=["Inspections"])


@router.get("/", response_model=List[InspectionRead])
async def list_inspections(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN)),
):
    """List all inspections."""
    from sqlalchemy import select
    from app.models.inspection import Inspection
    query = select(Inspection).limit(100)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/", response_model=InspectionRead)
async def create_inspection(
    data: InspectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN)),
):
    """Create a new inspection."""
    return await InspectionService.create_inspection(db, data, current_user.id)


@router.get("/issue/{issue_id}", response_model=List[InspectionRead])
async def list_for_issue(
    issue_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN)),
):
    """Get all inspections for a specific issue."""
    return await InspectionService.list_for_issue(db, issue_id)


@router.get("/{inspection_id}", response_model=InspectionRead)
async def get_inspection(
    inspection_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN)),
):
    """Get inspection details."""
    inspection = await InspectionService.get_by_id(db, inspection_id)
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return inspection


@router.patch("/{inspection_id}", response_model=InspectionRead)
async def update_inspection(
    inspection_id: int,
    data: InspectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN)),
):
    """Update inspection details."""
    inspection = await InspectionService.update_inspection(db, inspection_id, data)
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return inspection


@router.post("/{inspection_id}/complete", response_model=InspectionRead)
async def complete_inspection(
    inspection_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN)),
):
    """Mark an inspection as complete."""
    inspection = await InspectionService.complete_inspection(db, inspection_id, current_user.id)
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return inspection
