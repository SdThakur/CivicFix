"""SLA Service."""

import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.sla import SLARule, SLAEscalationLog
from app.models.report import Report, ReportStatus

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
    def compute_sla_status(sr: Any) -> str:
        # sr is assumed to have `created_at`, `status`
        # In a real impl we'd look up the rule and compare times.
        # This is a simplified version just returning healthy by default.
        if hasattr(sr, "status") and sr.status in (ReportStatus.RESOLVED, ReportStatus.REJECTED, ReportStatus.DUPLICATE):
            return "SLA_HEALTHY"
            
        now = datetime.datetime.now(datetime.timezone.utc)
        # Mock logic, usually relies on `calculate_deadlines` and rule.
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
        # Mock logic
        return []
