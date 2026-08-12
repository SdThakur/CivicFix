"""Service Request business logic."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.service_request import (
    ServiceRequest,
    ServiceRequestStatus,
    ServiceRequestStatusHistory,
)
from app.models.issue import Issue, IssuePriority


class ServiceRequestService:
    @staticmethod
    async def generate_sr_number(db: AsyncSession) -> str:
        query = select(func.max(ServiceRequest.id))
        result = await db.execute(query)
        max_id = result.scalar() or 0
        year = datetime.now(timezone.utc).year
        return f"SR-{year}-{(max_id + 1):06d}"

    @staticmethod
    async def create_from_issue(
        db: AsyncSession, issue_id: int, reporter_id: Optional[int] = None
    ) -> ServiceRequest:
        # Get the issue to determine priority
        issue_query = select(Issue).where(Issue.id == issue_id)
        result = await db.execute(issue_query)
        issue = result.scalar_one_or_none()
        
        if not issue:
            raise ValueError(f"Issue with id {issue_id} not found.")

        now = datetime.now(timezone.utc)
        
        # Calculate SLA based on priority
        response_hours = 0
        resolution_hours = 0
        if issue.priority == IssuePriority.URGENT or str(issue.priority).upper() == "CRITICAL":
            response_hours = 2
            resolution_hours = 24
        elif issue.priority == IssuePriority.HIGH:
            response_hours = 24
            resolution_hours = 72
        elif issue.priority == IssuePriority.MEDIUM:
            response_hours = 72
            resolution_hours = 336 # 14 days
        elif issue.priority == IssuePriority.LOW:
            response_hours = 168 # 7 days
            resolution_hours = 720 # 30 days
            
        sla_response_due_at = now + timedelta(hours=response_hours)
        sla_resolution_due_at = now + timedelta(hours=resolution_hours)

        sr_number = await ServiceRequestService.generate_sr_number(db)
        
        sr = ServiceRequest(
            sr_number=sr_number,
            issue_id=issue_id,
            reported_by_id=reporter_id,
            department_id=issue.department_id,
            status=ServiceRequestStatus.SUBMITTED,
            sla_response_due_at=sla_response_due_at,
            sla_resolution_due_at=sla_resolution_due_at,
        )
        
        db.add(sr)
        await db.commit()
        await db.refresh(sr)
        
        # Add initial history
        history = ServiceRequestStatusHistory(
            service_request_id=sr.id,
            changed_by_id=reporter_id,
            from_status=None,
            to_status=ServiceRequestStatus.SUBMITTED.value,
            notes="Service Request created from Issue."
        )
        db.add(history)
        await db.commit()
        await db.refresh(sr)
        
        return sr

    @staticmethod
    async def update_status(
        db: AsyncSession, sr_id: int, new_status: ServiceRequestStatus, changed_by_id: Optional[int], notes: Optional[str] = None
    ) -> ServiceRequest:
        query = select(ServiceRequest).where(ServiceRequest.id == sr_id)
        result = await db.execute(query)
        sr = result.scalar_one_or_none()
        
        if not sr:
            raise ValueError(f"Service Request with id {sr_id} not found.")
            
        old_status = sr.status
        if old_status == new_status:
            return sr
            
        sr.status = new_status
        now = datetime.now(timezone.utc)
        
        if new_status == ServiceRequestStatus.ACKNOWLEDGED and not sr.acknowledged_at:
            sr.acknowledged_at = now
        elif new_status == ServiceRequestStatus.VERIFIED and not sr.verified_at:
            sr.verified_at = now
        elif new_status == ServiceRequestStatus.ASSIGNED and not sr.assigned_at:
            sr.assigned_at = now
        elif new_status == ServiceRequestStatus.IN_PROGRESS and not sr.work_started_at:
            sr.work_started_at = now
        elif new_status == ServiceRequestStatus.RESOLVED and not sr.resolved_at:
            sr.resolved_at = now
        elif new_status in (ServiceRequestStatus.CLOSED, ServiceRequestStatus.REJECTED) and not sr.closed_at:
            sr.closed_at = now
            
        history = ServiceRequestStatusHistory(
            service_request_id=sr.id,
            changed_by_id=changed_by_id,
            from_status=old_status.value,
            to_status=new_status.value,
            notes=notes
        )
        db.add(history)
        await db.commit()
        await db.refresh(sr)
        return sr

    @staticmethod
    def check_sla_status(sr: ServiceRequest) -> str:
        now = datetime.now(timezone.utc)
        
        if sr.status in (ServiceRequestStatus.RESOLVED, ServiceRequestStatus.CLOSED, ServiceRequestStatus.REJECTED):
            return "SLA_HEALTHY"
            
        due_date = sr.sla_resolution_due_at
        if not due_date:
            return "SLA_HEALTHY"
            
        if now > due_date:
            return "BREACHED"
            
        created = sr.created_at
        total_duration = (due_date - created).total_seconds()
        remaining_duration = (due_date - now).total_seconds()
        
        # Approaching if within 20% of window
        if remaining_duration <= (0.2 * total_duration):
            return "APPROACHING_BREACH"
            
        return "SLA_HEALTHY"

    @staticmethod
    async def get_by_sr_number(db: AsyncSession, sr_number: str) -> Optional[ServiceRequest]:
        query = select(ServiceRequest).where(ServiceRequest.sr_number == sr_number)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_issue_id(db: AsyncSession, issue_id: int) -> Optional[ServiceRequest]:
        query = select(ServiceRequest).where(ServiceRequest.issue_id == issue_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_service_requests(
        db: AsyncSession, skip: int = 0, limit: int = 100, status: Optional[ServiceRequestStatus] = None, department_id: Optional[int] = None
    ) -> List[ServiceRequest]:
        query = select(ServiceRequest)
        if status:
            query = query.where(ServiceRequest.status == status)
        if department_id:
            query = query.where(ServiceRequest.department_id == department_id)
            
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_overdue_sla(db: AsyncSession) -> List[ServiceRequest]:
        query = select(ServiceRequest).where(ServiceRequest.sla_status == "BREACHED")
        result = await db.execute(query)
        return list(result.scalars().all())
