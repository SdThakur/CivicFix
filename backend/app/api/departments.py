"""Departments API Router."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_active_user, require_roles
from app.models.department import Department
from app.models.user import User, UserRole
from app.schemas.department import (
    DepartmentCreate,
    DepartmentResponse,
)

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("/", response_model=List[DepartmentResponse])
async def list_departments(
    db: AsyncSession = Depends(get_db),
) -> List[DepartmentResponse]:
    """List all municipal departments."""
    result = await db.execute(select(Department).order_by(Department.id.asc()))
    depts = list(result.scalars().all())
    return [DepartmentResponse.model_validate(d) for d in depts]


@router.post(
    "/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED
)
async def create_department(
    dept_in: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> DepartmentResponse:
    """Create a new department (Admin only)."""
    # Check duplicate code
    existing = await db.execute(
        select(Department).where(Department.code == dept_in.code)
    )
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Department code '{dept_in.code}' already exists.",
        )

    dept = Department(
        name=dept_in.name,
        code=dept_in.code,
        description=dept_in.description,
        contact_email=dept_in.contact_email,
        phone=dept_in.phone,
    )
    db.add(dept)
    await db.flush()
    await db.refresh(dept)
    return DepartmentResponse.model_validate(dept)


@router.get("/{dept_id}", response_model=DepartmentResponse)
async def get_department(
    dept_id: int, db: AsyncSession = Depends(get_db)
) -> DepartmentResponse:
    """Get department details by ID."""
    result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = result.scalars().first()
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Department not found."
        )
    return DepartmentResponse.model_validate(dept)
