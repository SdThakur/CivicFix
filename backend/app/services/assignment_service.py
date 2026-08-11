"""Service for Intelligent Work Assignment."""

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.work_order import WorkOrder
from app.models.crew import Crew
from app.models.report import Report, ReportCategory
from app.models.equipment import Equipment

# SLA status values (stored as plain strings on ServiceRequest)
SLA_HEALTHY = "SLA_HEALTHY"
SLA_APPROACHING = "APPROACHING_BREACH"
SLA_BREACHED = "BREACHED"


@dataclass
class AssignmentRecommendation:
    recommended_crew_id: int
    recommended_crew_name: str
    total_score: float
    distance_km: float
    reasons: List[str]
    score_breakdown: Dict[str, float]
    alternative_crews: List[Dict[str, Any]]
    can_meet_sla: bool
    estimated_response_minutes: int


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class AssignmentService:
    @staticmethod
    def recommend_crew(
        db: AsyncSession, 
        work_order: WorkOrder, 
        issue: Report, 
        available_crews: List[Crew], 
        equipment_list: List[Equipment]
    ) -> AssignmentRecommendation:
        
        # Skill mapping
        skill_map = {
            ReportCategory.POTHOLE: "asphalt",
            ReportCategory.STREETLIGHT: "electrical",
            ReportCategory.GRAFFITI: "cleaning",
            ReportCategory.TRASH: "cleaning",
            ReportCategory.ILLEGAL_DUMPING: "heavy_machinery",
            ReportCategory.SIDEWALK_DAMAGE: "concrete",
            ReportCategory.TREE_ISSUE: "arboriculture",
            ReportCategory.SIGN_DAMAGE: "signage",
            ReportCategory.WATER_LEAK: "plumbing",
        }
        
        required_skill = skill_map.get(issue.category) if hasattr(issue, 'category') else None
        # fallback to category name if missing enum support
        if required_skill is None and hasattr(issue, 'category'):
             if isinstance(issue.category, str):
                 try:
                     req_cat = ReportCategory(issue.category)
                     required_skill = skill_map.get(req_cat)
                 except ValueError:
                     pass

        crew_scores = []

        for crew in available_crews:
            reasons = []
            breakdown = {}

            # 1. Distance score (0-30)
            if hasattr(crew, 'latitude') and crew.latitude and hasattr(issue, 'latitude') and issue.latitude:
                dist_km = haversine_km(crew.latitude, crew.longitude, issue.latitude, issue.longitude)
            else:
                dist_km = 0.0 # Default if no loc
            
            if dist_km <= 0:
                dist_score = 30.0
                reasons.append("Crew is extremely close to the location.")
            elif dist_km >= 10.0:
                dist_score = 0.0
                reasons.append(f"Crew is {dist_km:.1f}km away.")
            else:
                dist_score = max(0.0, 30.0 * (1 - (dist_km / 10.0)))
                reasons.append(f"Crew is within {dist_km:.1f}km.")
            
            breakdown['distance_score'] = round(dist_score, 2)

            # 2. Availability score (0-25)
            active_jobs = getattr(crew, 'active_jobs', 0)
            max_jobs = getattr(crew, 'max_concurrent_jobs', 5)
            if max_jobs <= 0: max_jobs = 1
            
            avail_score = max(0.0, ((max_jobs - active_jobs) / max_jobs) * 25.0)
            breakdown['availability_score'] = round(avail_score, 2)
            if active_jobs == 0:
                reasons.append("Crew has full availability.")

            # 3. Workload score (0-20)
            pending = getattr(crew, 'pending_jobs', 0)
            if pending >= 5:
                workload_score = 0.0
            else:
                workload_score = 20.0 * (1 - (pending / 5.0))
            breakdown['workload_score'] = round(workload_score, 2)

            # 4. Skill match score (0-15)
            skill_score = 0.0
            crew_skills = getattr(crew, 'skills', [])
            if required_skill:
                if required_skill in crew_skills or any(required_skill in s for s in crew_skills):
                    skill_score = 15.0
                    reasons.append(f"Crew has required skill: {required_skill}.")
            else:
                # If no specific skill required, give partial credit
                skill_score = 7.5
            breakdown['skill_score'] = round(skill_score, 2)

            # 5. SLA urgency bonus (0-10)
            sla_bonus = 0.0
            if hasattr(work_order, 'sla_status'):
                if work_order.sla_status == SLABreachStatus.APPROACHING_BREACH:
                    sla_bonus = 5.0
                    reasons.append("SLA is approaching breach (bonus applied).")
                elif work_order.sla_status == SLABreachStatus.BREACHED:
                    sla_bonus = 10.0
                    reasons.append("SLA is breached (maximum urgency bonus applied).")
            breakdown['sla_bonus'] = sla_bonus

            total = sum(breakdown.values())
            
            # Estimates
            est_mins = int((dist_km / 30.0) * 60) + 15  # Assume 30km/h avg speed + 15 min prep
            can_meet = est_mins < 120 # simple heuristic
            
            crew_scores.append({
                'crew_id': crew.id,
                'crew_name': crew.name,
                'total_score': round(total, 2),
                'distance_km': round(dist_km, 2),
                'reasons': reasons,
                'score_breakdown': breakdown,
                'can_meet_sla': can_meet,
                'estimated_response_minutes': est_mins
            })

        if not crew_scores:
            return None

        # Sort by total score desc
        crew_scores.sort(key=lambda x: x['total_score'], reverse=True)
        top = crew_scores[0]
        alts = crew_scores[1:4]

        return AssignmentRecommendation(
            recommended_crew_id=top['crew_id'],
            recommended_crew_name=top['crew_name'],
            total_score=top['total_score'],
            distance_km=top['distance_km'],
            reasons=top['reasons'],
            score_breakdown=top['score_breakdown'],
            alternative_crews=alts,
            can_meet_sla=top['can_meet_sla'],
            estimated_response_minutes=top['estimated_response_minutes']
        )
    
    @staticmethod
    async def apply_recommendation(
        db: AsyncSession, 
        work_order_id: int, 
        crew_id: int, 
        assigned_by_id: int, 
        override_reason: Optional[str] = None
    ) -> WorkOrder:
        from app.models.work_order import WorkOrderStatus
        
        stmt = select(WorkOrder).where(WorkOrder.id == work_order_id)
        result = await db.execute(stmt)
        work_order = result.scalar_one_or_none()
        if not work_order:
            raise ValueError("Work order not found")
        
        work_order.crew_id = crew_id
        work_order.status = WorkOrderStatus.ASSIGNED
        # Note: audit logging would be added here
        
        await db.commit()
        await db.refresh(work_order)
        return work_order

    @staticmethod
    async def get_recommendation_for_work_order(db: AsyncSession, work_order_id: int) -> AssignmentRecommendation:
        # Load WO and Issue
        stmt = select(WorkOrder).options(selectinload(WorkOrder.issue)).where(WorkOrder.id == work_order_id)
        result = await db.execute(stmt)
        work_order = result.scalar_one_or_none()
        if not work_order or not work_order.issue:
            raise ValueError("Work order or associated issue not found")
            
        # Get all crews
        stmt = select(Crew)
        crews = (await db.execute(stmt)).scalars().all()
        
        return AssignmentService.recommend_crew(
            db=db,
            work_order=work_order,
            issue=work_order.issue,
            available_crews=list(crews),
            equipment_list=[]
        )
