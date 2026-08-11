"""Inspection database model."""

from datetime import datetime, timezone
import enum
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.issue import Issue
    from app.models.service_request import ServiceRequest


class InspectionStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class SafetyRiskLevel(str, enum.Enum):
    NONE = "NONE"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    IMMEDIATE_HAZARD = "IMMEDIATE_HAZARD"


class RepairRecommendation(str, enum.Enum):
    MONITORING = "MONITORING"
    ROUTINE_REPAIR = "ROUTINE_REPAIR"
    URGENT_REPAIR = "URGENT_REPAIR"
    EMERGENCY_REPAIR = "EMERGENCY_REPAIR"
    DECOMMISSION = "DECOMMISSION"
    FURTHER_INVESTIGATION = "FURTHER_INVESTIGATION"


class Inspection(Base):
    """Human inspection record for a reported issue."""

    __tablename__ = "inspections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    inspection_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    service_request_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("service_requests.id", ondelete="SET NULL"), nullable=True, index=True
    )
    issue_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("issues.id", ondelete="SET NULL"), nullable=True, index=True
    )
    inspector_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[InspectionStatus] = mapped_column(
        SQLEnum(InspectionStatus, native_enum=False),
        default=InspectionStatus.SCHEDULED,
        nullable=False,
    )

    # AI Input
    ai_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ai_severity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ai_priority_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Official Inspector Determination
    confirmed_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confirmed_severity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    safety_risk: Mapped[SafetyRiskLevel] = mapped_column(
        SQLEnum(SafetyRiskLevel, native_enum=False),
        default=SafetyRiskLevel.NONE,
        nullable=False,
    )
    is_emergency: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    lanes_affected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_area_sqm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    depth_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    road_condition_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    surface_type_found: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    recommended_repair: Mapped[Optional[RepairRecommendation]] = mapped_column(
        SQLEnum(RepairRecommendation, native_enum=False), nullable=True
    )
    estimated_repair_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    estimated_material_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    estimated_labor_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    inspection_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    photo_urls: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

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
    service_request: Mapped[Optional["ServiceRequest"]] = relationship(
        "ServiceRequest", back_populates="inspections"
    )
    issue: Mapped[Optional["Issue"]] = relationship("Issue")
    inspector: Mapped[Optional["User"]] = relationship("User")
