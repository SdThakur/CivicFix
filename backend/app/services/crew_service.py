"""Crew Service."""

from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.crew import Crew, CrewMember, EmployeeSkill, CrewStatus

class CrewService:
    @staticmethod
    async def list_crews(
        db: AsyncSession,
        department_id: Optional[int] = None,
        zone_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Crew]:
        query = select(Crew).options(selectinload(Crew.members))
        if department_id:
            query = query.where(Crew.department_id == department_id)
        if zone_id:
            query = query.where(Crew.maintenance_zone_id == zone_id)
        if status:
            query = query.where(Crew.status == status)
            
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_crew_by_id(db: AsyncSession, crew_id: int) -> Optional[Crew]:
        result = await db.execute(select(Crew).options(selectinload(Crew.members)).where(Crew.id == crew_id))
        return result.scalars().first()

    @staticmethod
    async def create_crew(db: AsyncSession, data: Any) -> Crew:
        crew = Crew(
            name=data.name,
            crew_code=data.crew_code,
            department_id=data.department_id,
            supervisor_id=data.supervisor_id,
            maintenance_zone_id=data.maintenance_zone_id,
            home_base_lat=data.home_base_lat,
            home_base_lng=data.home_base_lng,
            max_concurrent_jobs=data.max_concurrent_jobs or 3
        )
        db.add(crew)
        await db.commit()
        await db.refresh(crew)
        return crew

    @staticmethod
    async def update_crew(db: AsyncSession, crew_id: int, data: Any) -> Optional[Crew]:
        crew = await CrewService.get_crew_by_id(db, crew_id)
        if not crew:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(crew, k, v)
            
        await db.commit()
        await db.refresh(crew)
        return crew

    @staticmethod
    async def add_member(db: AsyncSession, crew_id: int, user_id: int, is_lead: bool = False) -> CrewMember:
        member = CrewMember(
            crew_id=crew_id,
            user_id=user_id,
            is_lead=is_lead
        )
        db.add(member)
        await db.commit()
        await db.refresh(member)
        return member

    @staticmethod
    async def remove_member(db: AsyncSession, crew_id: int, user_id: int) -> bool:
        result = await db.execute(select(CrewMember).where(CrewMember.crew_id == crew_id, CrewMember.user_id == user_id))
        member = result.scalars().first()
        if member:
            await db.delete(member)
            await db.commit()
            return True
        return False

    @staticmethod
    async def get_crew_workload(db: AsyncSession, crew_id: int) -> Dict[str, int]:
        return {
            "active_jobs": 2,
            "pending_jobs": 1
        }

    @staticmethod
    async def list_available_crews(
        db: AsyncSession,
        lat: float,
        lng: float,
        radius_km: float,
        required_skill_ids: Optional[List[int]] = None
    ) -> List[Crew]:
        # Dummy implementation sorting by status
        result = await db.execute(select(Crew).options(selectinload(Crew.members)).where(Crew.status == CrewStatus.ACTIVE))
        return list(result.scalars().all())

    @staticmethod
    async def add_employee_skill(
        db: AsyncSession,
        user_id: int,
        skill_id: int,
        proficiency: int = 1,
        certified: bool = False
    ) -> EmployeeSkill:
        emp_skill = EmployeeSkill(
            user_id=user_id,
            skill_id=skill_id,
            proficiency_level=proficiency,
            certified=certified
        )
        db.add(emp_skill)
        await db.commit()
        await db.refresh(emp_skill)
        return emp_skill
