"""Preventive maintenance database models."""

from datetime import datetime, timezone
import enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum as SQLEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.asset import InfrastructureAsset, RoadSegment, Road
    from app.models.user import User
    from app.models.work_order import WorkOrder


class MaintenanceRecommendationStatus(str, enum.Enum):
    """Status for preventive maintenance recommendation."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"


class MaintenanceType(str, enum.Enum):
    """Type of maintenance recommended."""

    ROUTINE_INSPECTION = "ROUTINE_INSPECTION"
    PREVENTIVE_REPAIR = "PREVENTIVE_REPAIR"
    FULL_REHABILITATION = "FULL_REHABILITATION"
    EMERGENCY_PATCHING = "EMERGENCY_PATCHING"
    SURFACE_TREATMENT = "SURFACE_TREATMENT"


class MaintenanceRecommendation(Base):
    """Preventive maintenance recommendation."""

    __tablename__ = "maintenance_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rec_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    
    asset_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("infrastructure_assets.id", ondelete="SET NULL"), nullable=True
    )
    road_segment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("road_segments.id", ondelete="SET NULL"), nullable=True
    )
    road_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("roads.id", ondelete="SET NULL"), nullable=True
    )
    
    maintenance_type: Mapped[MaintenanceType] = mapped_column(
        SQLEnum(MaintenanceType, native_enum=False), nullable=False
    )
    status: Mapped[MaintenanceRecommendationStatus] = mapped_column(
        SQLEnum(MaintenanceRecommendationStatus, native_enum=False), 
        default=MaintenanceRecommendationStatus.PENDING, 
        nullable=False
    )
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    
    risk_score_at_creation: Mapped[float] = mapped_column(Float, nullable=False)
    incident_count_trigger: Mapped[int] = mapped_column(Integer, nullable=False)
    days_since_last_maintenance: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estimated_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    priority: Mapped[str] = mapped_column(String(50), default="HIGH", nullable=False)
    recommended_by: Mapped[str] = mapped_column(String(100), default="SYSTEM", nullable=False)
    
    approved_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    scheduled_work_order_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("work_orders.id", ondelete="SET NULL"), nullable=True
    )
    due_by: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    asset: Mapped[Optional["InfrastructureAsset"]] = relationship(
        "InfrastructureAsset", foreign_keys=[asset_id]
    )
    road_segment: Mapped[Optional["RoadSegment"]] = relationship(
        "RoadSegment", foreign_keys=[road_segment_id]
    )
    road: Mapped[Optional["Road"]] = relationship(
        "Road", foreign_keys=[road_id]
    )
    approved_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[approved_by_id]
    )
    scheduled_work_order: Mapped[Optional["WorkOrder"]] = relationship(
        "WorkOrder", foreign_keys=[scheduled_work_order_id]
    )
