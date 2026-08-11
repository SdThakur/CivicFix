"""Service for Risk Scoring."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timezone, timedelta

from app.models.asset import InfrastructureAsset, RoadSegment
from app.models.report import Report


@dataclass
class RiskScoreResult:
    score: float
    label: str
    factors: Dict[str, float]
    explanation: List[str]


class RiskScoringService:
    @staticmethod
    def get_label_for_score(score: float) -> str:
        if score <= 20:
            return "VERY_LOW"
        elif score <= 40:
            return "LOW"
        elif score <= 60:
            return "MODERATE"
        elif score <= 80:
            return "HIGH"
        return "CRITICAL"

    @staticmethod
    def calculate_asset_risk(db: AsyncSession, asset_or_road_segment: Any, recent_reports: List[Report]) -> RiskScoreResult:
        factors = {}
        explanation = []
        
        # 1. Incident frequency (30%)
        incident_count = len(recent_reports)
        freq_score = min(30.0, (incident_count / 10.0) * 30.0)
        factors['incident_frequency'] = round(freq_score, 2)
        if incident_count > 0:
            explanation.append(f"{incident_count} incident(s) in last 90 days.")
        
        # 2. Incident severity (25%)
        # Map PriorityLevel to severity scores
        # Default PriorityLevel: CRITICAL, HIGH, MEDIUM, LOW
        severity_map = {
            "CRITICAL": 25.0,
            "HIGH": 20.0,
            "MEDIUM": 12.0,
            "LOW": 5.0
        }
        if incident_count > 0:
            total_sev = 0.0
            for r in recent_reports:
                pri = r.priority.value if hasattr(r.priority, 'value') else r.priority
                total_sev += severity_map.get(str(pri).upper(), 5.0)
            avg_sev = total_sev / incident_count
            sev_score = min(25.0, avg_sev)
            explanation.append(f"Average incident severity score: {avg_sev:.1f}/25.")
        else:
            sev_score = 0.0
        factors['incident_severity'] = round(sev_score, 2)
        
        # 3. Traffic impact & road class (20%)
        # Assuming road class string exists on the asset/segment
        road_class = getattr(asset_or_road_segment, 'road_class', getattr(asset_or_road_segment, 'asset_type', ''))
        road_class = str(road_class).upper()
        
        if 'INTERSTATE' in road_class:
            traf_score = 20.0
        elif 'US_ROUTE' in road_class or 'HIGHWAY' in road_class:
            traf_score = 17.0
        elif 'STATE_ROUTE' in road_class:
            traf_score = 14.0
        elif 'COUNTY' in road_class:
            traf_score = 10.0
        elif 'MUNICIPAL' in road_class or 'STREET' in road_class:
            traf_score = 8.0
        elif 'PRIVATE' in road_class:
            traf_score = 3.0
        else:
            traf_score = 10.0 # Default
            
        factors['traffic_impact'] = round(traf_score, 2)
        explanation.append(f"Traffic impact based on class/type: {traf_score} pts.")
        
        # 4. Asset physical condition (15%)
        cond = getattr(asset_or_road_segment, 'condition_score', 100.0)
        # 100 = 0 pts, 0 = 15 pts
        cond_score = max(0.0, min(15.0, 15.0 * (1 - (cond / 100.0))))
        factors['physical_condition'] = round(cond_score, 2)
        explanation.append(f"Condition score of {cond} gives {cond_score:.1f} pts risk.")
        
        # 5. Maintenance history (10%)
        last_maint = getattr(asset_or_road_segment, 'last_maintenance_date', None)
        if not last_maint:
            maint_score = 10.0
            explanation.append("No recent maintenance history available (max risk).")
        else:
            days_since = (datetime.now(timezone.utc) - last_maint).days
            if days_since < 30:
                maint_score = 0.0
            elif days_since <= 90:
                maint_score = 5.0
            elif days_since <= 180:
                maint_score = 8.0
            else:
                maint_score = 10.0
            explanation.append(f"Last maintenance {days_since} days ago gives {maint_score} pts risk.")
            
        factors['maintenance_history'] = round(maint_score, 2)
        
        total_score = sum(factors.values())
        return RiskScoreResult(
            score=round(total_score, 2),
            label=RiskScoringService.get_label_for_score(total_score),
            factors=factors,
            explanation=explanation
        )

    @staticmethod
    async def score_road_segment(db: AsyncSession, segment_id: int) -> RiskScoreResult:
        stmt = select(RoadSegment).where(RoadSegment.id == segment_id)
        result = await db.execute(stmt)
        segment = result.scalar_one_or_none()
        if not segment:
            raise ValueError("Segment not found")
            
        # Get reports near segment - placeholder logic, assuming segment has lat/lng or bounds
        # For this prototype we will just pull some generic recent reports
        ninety_days_ago = datetime.now(timezone.utc) - timedelta(days=90)
        stmt_reports = select(Report).where(Report.created_at >= ninety_days_ago).limit(10)
        reports = (await db.execute(stmt_reports)).scalars().all()
        
        score_res = RiskScoringService.calculate_asset_risk(db, segment, list(reports))
        
        # Save score
        segment.risk_score = score_res.score
        # Assumes label field exists, or just score
        await db.commit()
        
        return score_res

    @staticmethod
    async def score_all_segments(db: AsyncSession) -> List[Dict[str, Any]]:
        stmt = select(RoadSegment)
        segments = (await db.execute(stmt)).scalars().all()
        
        results = []
        for seg in segments:
            res = await RiskScoringService.score_road_segment(db, seg.id)
            results.append({"segment_id": seg.id, "score": res.score, "label": res.label})
            
        return results
        
    @staticmethod
    async def get_high_risk_segments(db: AsyncSession, threshold: float = 70.0, limit: int = 20) -> List[RoadSegment]:
        stmt = select(RoadSegment).where(RoadSegment.risk_score >= threshold).order_by(RoadSegment.risk_score.desc()).limit(limit)
        return list((await db.execute(stmt)).scalars().all())
        
    @staticmethod
    async def get_high_risk_assets(db: AsyncSession, threshold: float = 70.0, limit: int = 20) -> List[InfrastructureAsset]:
        stmt = select(InfrastructureAsset).where(InfrastructureAsset.risk_score >= threshold).order_by(InfrastructureAsset.risk_score.desc()).limit(limit)
        return list((await db.execute(stmt)).scalars().all())
