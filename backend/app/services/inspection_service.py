"""Inspection business logic."""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.inspection import Inspection, InspectionStatus
from app.schemas.inspection import InspectionCreate, InspectionUpdate
from app.services.service_request_service import ServiceRequestService
from app.models.service_request import ServiceRequestStatus


class InspectionService:
    @staticmethod
    async def generate_inspection_number(db: AsyncSession) -> str:
        query = select(func.max(Inspection.id))
        result = await db.execute(query)
        max_id = result.scalar() or 0
        year = datetime.now(timezone.utc).year
        return f"INS-{year}-{(max_id + 1):06d}"

    @staticmethod
    async def create_inspection(
        db: AsyncSession, data: InspectionCreate, inspector_id: Optional[int]
    ) -> Inspection:
        ins_number = await InspectionService.generate_inspection_number(db)
        inspection = Inspection(
            inspection_number=ins_number,
            service_request_id=data.service_request_id,
            issue_id=data.issue_id,
            inspector_id=inspector_id,
            ai_category=data.ai_category,
            ai_severity=data.ai_severity,
            ai_priority_score=data.ai_priority_score,
            status=InspectionStatus.SCHEDULED,
        )
        db.add(inspection)
        await db.commit()
        await db.refresh(inspection)
        
        # update SR if exists
        if data.service_request_id:
            await ServiceRequestService.update_status(
                db, data.service_request_id, ServiceRequestStatus.UNDER_INSPECTION, inspector_id, "Inspection scheduled."
            )
            
        return inspection

    @staticmethod
    async def update_inspection(
        db: AsyncSession, inspection_id: int, data: InspectionUpdate
    ) -> Optional[Inspection]:
        query = select(Inspection).where(Inspection.id == inspection_id)
        result = await db.execute(query)
        inspection = result.scalar_one_or_none()
        
        if not inspection:
            return None
            
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(inspection, key, value)
            
        await db.commit()
        await db.refresh(inspection)
        return inspection

    @staticmethod
    async def complete_inspection(
        db: AsyncSession, inspection_id: int, inspector_id: int
    ) -> Optional[Inspection]:
        query = select(Inspection).where(Inspection.id == inspection_id)
        result = await db.execute(query)
        inspection = result.scalar_one_or_none()
        
        if not inspection:
            return None
            
        inspection.status = InspectionStatus.COMPLETED
        inspection.completed_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(inspection)
        
        if inspection.service_request_id:
            await ServiceRequestService.update_status(
                db, inspection.service_request_id, ServiceRequestStatus.VERIFIED, inspector_id, "Inspection completed and verified."
            )
            
        return inspection

    @staticmethod
    async def get_by_id(db: AsyncSession, id: int) -> Optional[Inspection]:
        query = select(Inspection).where(Inspection.id == id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_for_issue(db: AsyncSession, issue_id: int) -> List[Inspection]:
        query = select(Inspection).where(Inspection.issue_id == issue_id)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def list_for_inspector(db: AsyncSession, inspector_id: int) -> List[Inspection]:
        query = select(Inspection).where(Inspection.inspector_id == inspector_id)
        result = await db.execute(query)
        return list(result.scalars().all())
