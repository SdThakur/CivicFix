"""Crews API Router."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.models.crew import Skill
from app.schemas.crew import (
    CrewRead, CrewCreate, CrewUpdate, 
    CrewMemberAdd, SkillRead, EmployeeSkillCreate
)
from app.services.crew_service import CrewService

router = APIRouter(prefix="/crews", tags=["Crews"])

@router.get("/", response_model=List[CrewRead])
async def list_crews(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN]))
) -> List[CrewRead]:
    """List crews."""
    crews = await CrewService.list_crews(db)
    return [CrewRead.model_validate(c) for c in crews]

@router.post("/", response_model=CrewRead, status_code=status.HTTP_201_CREATED)
async def create_crew(
    crew_in: CrewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN]))
) -> CrewRead:
    """Create a crew."""
    crew = await CrewService.create_crew(db, crew_in)
    return CrewRead.model_validate(crew)

@router.get("/available", response_model=List[CrewRead])
async def list_available_crews(
    lat: float,
    lng: float,
    radius_km: float = 10.0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN]))
) -> List[CrewRead]:
    """List available crews near location."""
    crews = await CrewService.list_available_crews(db, lat, lng, radius_km)
    return [CrewRead.model_validate(c) for c in crews]

@router.get("/skills", response_model=List[SkillRead])
async def list_skills(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN]))
) -> List[SkillRead]:
    """List all skills."""
    result = await db.execute(select(Skill))
    skills = list(result.scalars().all())
    return [SkillRead.model_validate(s) for s in skills]

@router.post("/skills", response_model=SkillRead, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill_in: dict,  # Simplification
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
) -> SkillRead:
    """Create skill."""
    skill = Skill(**skill_in)
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    return SkillRead.model_validate(skill)

@router.get("/{crew_id}", response_model=CrewRead)
async def get_crew(
    crew_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN]))
) -> CrewRead:
    """Get crew by ID."""
    crew = await CrewService.get_crew_by_id(db, crew_id)
    if not crew:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crew not found")
    return CrewRead.model_validate(crew)

@router.patch("/{crew_id}", response_model=CrewRead)
async def update_crew(
    crew_id: int,
    crew_in: CrewUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN]))
) -> CrewRead:
    """Update crew."""
    crew = await CrewService.update_crew(db, crew_id, crew_in)
    if not crew:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crew not found")
    return CrewRead.model_validate(crew)

@router.post("/{crew_id}/members", status_code=status.HTTP_200_OK)
async def add_crew_member(
    crew_id: int,
    member_in: CrewMemberAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN]))
):
    """Add member to crew."""
    await CrewService.add_member(db, crew_id, member_in.user_id, member_in.is_lead)
    return {"status": "ok"}

@router.delete("/{crew_id}/members/{user_id}", status_code=status.HTTP_200_OK)
async def remove_crew_member(
    crew_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN]))
):
    """Remove member from crew."""
    success = await CrewService.remove_member(db, crew_id, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found in crew")
    return {"status": "ok"}

@router.get("/{crew_id}/workload", response_model=Dict[str, int])
async def get_crew_workload(
    crew_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.STAFF, UserRole.MANAGER, UserRole.ADMIN]))
) -> Dict[str, int]:
    """Get crew workload."""
    return await CrewService.get_crew_workload(db, crew_id)

