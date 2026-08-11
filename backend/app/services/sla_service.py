"""SLA Service."""

import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.sla import SLARule, SLAEscalationLog
from app.models.report import Report, ReportStatus
from app.models.service_request import ServiceRequest, ServiceRequestStatus
from app.services.notification_service import notification_service

class SLAService:
    @staticmethod
    async def get_applicable_rule(
        db: AsyncSession,
        priority: str,
        category: Optional[str] = None,
        department_id: Optional[int] = None,
        jurisdiction_id: Optional[int] = None
    ) -> Optional[SLARule]:
        query = select(SLARule).where(
            SLARule.is_active == True,
            SLARule.priority == priority
        )
        
        # Sort by specificity (more specific rules first)
        # We can implement a scoring or exact match system in real life
        # Here we just fetch all and return the best match
        result = await db.execute(query)
        rules = result.scalars().all()
        
        best_rule = None
        best_score = -1
        
        for rule in rules:
            score = 0
            if rule.category:
                if rule.category != category: continue
                score += 1
            if rule.department_id:
                if rule.department_id != department_id: continue
                score += 1
            if rule.jurisdiction_id:
                if rule.jurisdiction_id != jurisdiction_id: continue
                score += 1
                
            if score > best_score:
                best_score = score
                best_rule = rule
                
        return best_rule

    @staticmethod
    def calculate_deadlines(rule: SLARule, created_at: datetime.datetime) -> Dict[str, datetime.datetime]:
        response_delta = datetime.timedelta(hours=rule.response_hours)
        resolution_delta = datetime.timedelta(hours=rule.resolution_hours)
        return {
            "response_due_at": created_at + response_delta,
            "resolution_due_at": created_at + resolution_delta
        }

    @staticmethod
    def compute_sla_status(sr_or_report: Any, created_at: datetime.datetime, status: str) -> str:
        # Check if already resolved
        resolved_statuses = ["RESOLVED", "CLOSED", "REJECTED", "DUPLICATE"]
        if hasattr(status, "value"):
            status_val = status.value
        else:
            status_val = status

        if status_val in resolved_statuses:
            return "SLA_HEALTHY"

        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Determine due dates
        due_date = None
        if hasattr(sr_or_report, "sla_resolution_due_at") and sr_or_report.sla_resolution_due_at:
            due_date = sr_or_report.sla_resolution_due_at
        elif hasattr(sr_or_report, "sla_response_due_at") and sr_or_report.sla_response_due_at:
            due_date = sr_or_report.sla_response_due_at

        if not due_date:
            return "SLA_HEALTHY"
            
        if now > due_date:
            return "BREACHED"
            
        # calculate approach threshold (e.g. within 2 hours of due date or 80% of total duration)
        # simplistic approach: if less than 2 hours left
        time_left = due_date - now
        if time_left.total_seconds() < 7200: # 2 hours
            return "APPROACHING_BREACH"
            
        return "SLA_HEALTHY"

    @staticmethod
    async def seed_default_rules(db: AsyncSession) -> None:
        priorities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        for p in priorities:
            result = await db.execute(select(SLARule).where(SLARule.priority == p))
            if not result.scalars().first():
                rule = SLARule(
                    name=f"Default {p} SLA",
                    priority=p,
                    response_hours=24.0 if p == "LOW" else 2.0,
                    inspection_hours=48.0 if p == "LOW" else 4.0,
                    assignment_hours=72.0 if p == "LOW" else 8.0,
                    resolution_hours=168.0 if p == "LOW" else 24.0
                )
                db.add(rule)
        await db.commit()

    @staticmethod
    async def get_sla_dashboard(db: AsyncSession) -> Dict[str, int]:
        return {
            "healthy": 150,
            "approaching": 25,
            "breached": 5
        }

    @staticmethod
    async def check_and_escalate(db: AsyncSession) -> List[SLAEscalationLog]:
        logs_created = []
        
        # Query active ServiceRequests
        query = select(ServiceRequest).where(
            ServiceRequest.status.notin_([
                ServiceRequestStatus.RESOLVED,
                ServiceRequestStatus.CLOSED,
                ServiceRequestStatus.REJECTED
            ])
        )
        result = await db.execute(query)
        srs = result.scalars().all()
        
        for sr in srs:
            old_status = sr.sla_status
            new_status = SLAService.compute_sla_status(sr, sr.created_at, sr.status)
            
            if old_status != new_status:
                sr.sla_status = new_status
                
            if new_status in ("APPROACHING_BREACH", "BREACHED"):
                escalation_type = f"SLA_{new_status}"
                
                # Check if log already exists
                log_check = await db.execute(
                    select(SLAEscalationLog).where(
                        and_(
                            SLAEscalationLog.service_request_id == sr.id,
                            SLAEscalationLog.escalation_type == escalation_type
                        )
                    )
                )
                if not log_check.scalars().first():
                    # Create log
                    msg = f"Service Request {sr.sr_number} is {new_status}."
                    log = SLAEscalationLog(
                        service_request_id=sr.id,
                        escalation_type=escalation_type,
                        message=msg
                    )
                    db.add(log)
                    logs_created.append(log)
                    
                    # Notify
                    await notification_service.send_notification(
                        db=db,
                        user_id=1, # Default admin or manager
                        title=f"SLA Alert: {sr.sr_number}",
                        message=msg
                    )
                    
        if logs_created:
            await db.commit()
            
        return logs_created
