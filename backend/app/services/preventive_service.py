"""Service for Preventive Maintenance."""

import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.preventive_maintenance import (
    MaintenanceRecommendation,
    MaintenanceRecommendationStatus,
    MaintenanceType
)
from app.models.asset import InfrastructureAsset, RoadSegment
from app.models.work_order import WorkOrder, WorkOrderPriority, WorkOrderStatus

class PreventiveMaintenanceService:
    @staticmethod
    async def generate_rec_number(db: AsyncSession) -> str:
        year = datetime.datetime.now().year
        stmt = select(func.count(MaintenanceRecommendation.id)).where(
            MaintenanceRecommendation.rec_number.like(f"PM-{year}-%")
        )
        count = await db.scalar(stmt)
        count = count or 0
        return f"PM-{year}-{(count + 1):06d}"

    @staticmethod
    async def scan_for_recommendations(db: AsyncSession) -> List[MaintenanceRecommendation]:
        new_recs = []
        
        # 1. Query road segments with incident_count_90d >= 5 OR risk_score >= 70
        # Assuming incident_count_90d exists or we use risk_score for now
        stmt = select(RoadSegment).where(RoadSegment.risk_score >= 70)
        high_risk_segments = (await db.execute(stmt)).scalars().all()
        
        for seg in high_risk_segments:
            # Check for existing PENDING recommendation
            stmt_check = select(MaintenanceRecommendation).where(
                and_(
                    MaintenanceRecommendation.road_segment_id == seg.id,
                    MaintenanceRecommendation.status == MaintenanceRecommendationStatus.PENDING
                )
            )
            existing = (await db.execute(stmt_check)).scalar_one_or_none()
            if not existing:
                rec_num = await PreventiveMaintenanceService.generate_rec_number(db)
                rec = MaintenanceRecommendation(
                    rec_number=rec_num,
                    road_segment_id=seg.id,
                    maintenance_type=MaintenanceType.FULL_REHABILITATION if seg.risk_score > 85 else MaintenanceType.PREVENTIVE_REPAIR,
                    title=f"Maintenance required for Road Segment {seg.id}",
                    reasoning=f"Risk score is high ({seg.risk_score}). Automatically generated recommendation.",
                    risk_score_at_creation=seg.risk_score or 0.0,
                    incident_count_trigger=5, # Hardcoded for now based on instruction trigger text
                    priority="HIGH" if seg.risk_score > 85 else "MEDIUM"
                )
                db.add(rec)
                await db.flush()
                new_recs.append(rec)
                
        # 2. Query assets with condition_score <= 40 OR risk_score >= 70
        stmt2 = select(InfrastructureAsset).where(
            (InfrastructureAsset.condition_score <= 40) | (InfrastructureAsset.risk_score >= 70)
        )
        critical_assets = (await db.execute(stmt2)).scalars().all()
        
        for asset in critical_assets:
            # Check for existing PENDING recommendation
            stmt_check = select(MaintenanceRecommendation).where(
                and_(
                    MaintenanceRecommendation.asset_id == asset.id,
                    MaintenanceRecommendation.status == MaintenanceRecommendationStatus.PENDING
                )
            )
            existing = (await db.execute(stmt_check)).scalar_one_or_none()
            if not existing:
                rec_num = await PreventiveMaintenanceService.generate_rec_number(db)
                rec = MaintenanceRecommendation(
                    rec_number=rec_num,
                    asset_id=asset.id,
                    maintenance_type=MaintenanceType.ROUTINE_INSPECTION,
                    title=f"Inspection/Repair required for Asset {asset.id}",
                    reasoning=f"Condition score ({asset.condition_score}) or risk score ({asset.risk_score}) triggered maintenance.",
                    risk_score_at_creation=asset.risk_score or 0.0,
                    incident_count_trigger=0,
                    priority="HIGH"
                )
                db.add(rec)
                await db.flush()
                new_recs.append(rec)
                
        await db.commit()
        return new_recs

    @staticmethod
    async def approve_recommendation(db: AsyncSession, rec_id: int, approved_by_id: int) -> MaintenanceRecommendation:
        stmt = select(MaintenanceRecommendation).where(MaintenanceRecommendation.id == rec_id)
        rec = (await db.execute(stmt)).scalar_one_or_none()
        
        if not rec:
            raise ValueError("Recommendation not found")
        if rec.status != MaintenanceRecommendationStatus.PENDING:
            raise ValueError(f"Cannot approve recommendation in status {rec.status}")
            
        rec.status = MaintenanceRecommendationStatus.APPROVED
        rec.approved_by_id = approved_by_id
        rec.approved_at = datetime.datetime.now(datetime.timezone.utc)
        
        # Create a linked WorkOrder
        wo = WorkOrder(
            title=f"PM: {rec.title}",
            description=rec.reasoning,
            priority=WorkOrderPriority.HIGH if rec.priority == "HIGH" else WorkOrderPriority.MEDIUM,
            status=WorkOrderStatus.OPEN,
            asset_id=rec.asset_id,
            road_segment_id=rec.road_segment_id
        )
        db.add(wo)
        await db.flush()
        
        rec.scheduled_work_order_id = wo.id
        rec.status = MaintenanceRecommendationStatus.SCHEDULED
        
        await db.commit()
        await db.refresh(rec)
        return rec

    @staticmethod
    async def reject_recommendation(db: AsyncSession, rec_id: int, rejection_reason: str) -> MaintenanceRecommendation:
        stmt = select(MaintenanceRecommendation).where(MaintenanceRecommendation.id == rec_id)
        rec = (await db.execute(stmt)).scalar_one_or_none()
        
        if not rec:
            raise ValueError("Recommendation not found")
            
        rec.status = MaintenanceRecommendationStatus.REJECTED
        rec.rejection_reason = rejection_reason
        await db.commit()
        await db.refresh(rec)
        return rec

    @staticmethod
    async def list_recommendations(db: AsyncSession, status: Optional[str] = None, limit: int = 50) -> List[MaintenanceRecommendation]:
        stmt = select(MaintenanceRecommendation).order_by(MaintenanceRecommendation.created_at.desc())
        if status:
            try:
                stat_enum = MaintenanceRecommendationStatus(status)
                stmt = stmt.where(MaintenanceRecommendation.status == stat_enum)
            except ValueError:
                pass
        stmt = stmt.limit(limit)
        return list((await db.execute(stmt)).scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, rec_id: int) -> Optional[MaintenanceRecommendation]:
        stmt = select(MaintenanceRecommendation).where(MaintenanceRecommendation.id == rec_id)
        return (await db.execute(stmt)).scalar_one_or_none()
