"""Service Request database model."""

from datetime import datetime, timezone
import enum
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.department import Department
    from app.models.issue import Issue
    from app.models.inspection import Inspection


class ServiceRequestStatus(str, enum.Enum):
    """Status of a 311 Service Request."""

    SUBMITTED = "SUBMITTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    UNDER_INSPECTION = "UNDER_INSPECTION"
    VERIFIED = "VERIFIED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"


class ServiceRequest(Base):
    """311 Service Request wrapping a canonical Issue."""

    __tablename__ = "service_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sr_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    issue_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("issues.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reported_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assigned_to_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[ServiceRequestStatus] = mapped_column(
        SQLEnum(ServiceRequestStatus, native_enum=False),
        default=ServiceRequestStatus.SUBMITTED,
        nullable=False,
    )
    citizen_facing_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority_override: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    inspection_scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    work_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sla_response_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sla_resolution_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    sla_status: Mapped[str] = mapped_column(String(50), default="SLA_HEALTHY", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    issue: Mapped["Issue"] = relationship("Issue", backref="service_requests")
    reported_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reported_by_id])
    assigned_to: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to_id])
    department: Mapped[Optional["Department"]] = relationship("Department")
    status_history: Mapped[List["ServiceRequestStatusHistory"]] = relationship(
        "ServiceRequestStatusHistory", back_populates="service_request", cascade="all, delete-orphan", lazy="selectin"
    )
    inspections: Mapped[List["Inspection"]] = relationship(
        "Inspection", back_populates="service_request"
    )


class ServiceRequestStatusHistory(Base):
    """History of status changes for a Service Request."""

    __tablename__ = "service_request_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    service_request_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("service_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    changed_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    from_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    to_status: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    service_request: Mapped["ServiceRequest"] = relationship(
        "ServiceRequest", back_populates="status_history"
    )
    changed_by: Mapped[Optional["User"]] = relationship("User")
