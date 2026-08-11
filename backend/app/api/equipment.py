"""Equipment API Router."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.models.equipment import Equipment, EquipmentType, EquipmentAssignment
from app.schemas.equipment import (
    EquipmentRead, EquipmentCreate, EquipmentUpdate,
    EquipmentTypeRead, EquipmentAssignmentCreate, EquipmentAssignmentRead
)

router = APIRouter(prefix="/equipment", tags=["Equipment"])

@router.get("/types", response_model=List[EquipmentTypeRead])
async def list_equipment_types(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN]))
) -> List[EquipmentTypeRead]:
    """List equipment types."""
    result = await db.execute(select(EquipmentType))
    types = list(result.scalars().all())
    return [EquipmentTypeRead.model_validate(t) for t in types]

@router.post("/types", response_model=EquipmentTypeRead, status_code=status.HTTP_201_CREATED)
async def create_equipment_type(
    type_in: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
) -> EquipmentTypeRead:
    """Create equipment type."""
    eq_type = EquipmentType(**type_in)
    db.add(eq_type)
    await db.commit()
    await db.refresh(eq_type)
    return EquipmentTypeRead.model_validate(eq_type)

@router.get("/", response_model=List[EquipmentRead])
async def list_equipment(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN]))
) -> List[EquipmentRead]:
    """List equipment."""
    query = select(Equipment)
    if status:
        query = query.where(Equipment.status == status)
    result = await db.execute(query)
    items = list(result.scalars().all())
    return [EquipmentRead.model_validate(i) for i in items]

@router.post("/", response_model=EquipmentRead, status_code=status.HTTP_201_CREATED)
async def create_equipment(
    eq_in: EquipmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN]))
) -> EquipmentRead:
    """Create equipment."""
    eq = Equipment(**eq_in.model_dump())
    db.add(eq)
    await db.commit()
    await db.refresh(eq)
    return EquipmentRead.model_validate(eq)

@router.post("/assignments", response_model=EquipmentAssignmentRead, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    assign_in: EquipmentAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN]))
) -> EquipmentAssignmentRead:
    """Assign equipment."""
    assignment = EquipmentAssignment(**assign_in.model_dump())
    assignment.assigned_by_id = current_user.id
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return EquipmentAssignmentRead.model_validate(assignment)

@router.get("/work-order/{work_order_id}", response_model=List[EquipmentAssignmentRead])
async def list_assignments_for_wo(
    work_order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN]))
) -> List[EquipmentAssignmentRead]:
    """List assignments for work order."""
    result = await db.execute(select(EquipmentAssignment).where(EquipmentAssignment.work_order_id == work_order_id))
    assignments = list(result.scalars().all())
    return [EquipmentAssignmentRead.model_validate(a) for a in assignments]


@router.get("/{equipment_id}", response_model=EquipmentRead)
async def get_equipment(
    equipment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN]))
) -> EquipmentRead:
    """Get equipment."""
    result = await db.execute(select(Equipment).where(Equipment.id == equipment_id))
    eq = result.scalars().first()
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return EquipmentRead.model_validate(eq)

@router.patch("/{equipment_id}", response_model=EquipmentRead)
async def update_equipment(
    equipment_id: int,
    eq_in: EquipmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN]))
) -> EquipmentRead:
    """Update equipment."""
    result = await db.execute(select(Equipment).where(Equipment.id == equipment_id))
    eq = result.scalars().first()
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    update_data = eq_in.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(eq, k, v)
        
    await db.commit()
    await db.refresh(eq)
    return EquipmentRead.model_validate(eq)

    return EquipmentRead.model_validate(eq)
