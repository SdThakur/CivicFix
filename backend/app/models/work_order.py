"""WorkOrder database model."""

from datetime import datetime, timezone
import enum
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.report import PriorityLevel

if TYPE_CHECKING:
    from app.models.issue import Issue
    from app.models.department import Department
    from app.models.user import User
    from app.models.crew import Crew


class WorkOrderStatus(str, enum.Enum):
    """Work Order lifecycle status."""

    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


WorkOrderPriority = PriorityLevel


class WorkOrder(Base):
    """Work order assignment for maintenance field crews."""

    __tablename__ = "work_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    work_order_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    issue_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("issues.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[WorkOrderStatus] = mapped_column(
        SQLEnum(WorkOrderStatus, native_enum=False), default=WorkOrderStatus.PENDING, nullable=False, index=True
    )
    priority: Mapped[PriorityLevel] = mapped_column(
        SQLEnum(PriorityLevel, native_enum=False), default=PriorityLevel.MEDIUM, nullable=False
    )

    assigned_department_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    assigned_to_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    crew_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("crews.id", ondelete="SET NULL"), nullable=True
    )

    scheduled_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    scheduled_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actual_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actual_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    estimated_hours: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    actual_hours: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
    issue: Mapped["Issue"] = relationship("Issue", back_populates="work_orders")
    assigned_department: Mapped[Optional["Department"]] = relationship(
        "Department", back_populates="work_orders"
    )
    assigned_to: Mapped[Optional["User"]] = relationship(
        "User", back_populates="assigned_work_orders"
    )
    crew: Mapped[Optional["Crew"]] = relationship(
        "Crew", back_populates="work_orders"
    )
