"""Issue database model."""

from datetime import datetime, timezone
import enum
from typing import TYPE_CHECKING, List, Optional
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
from app.models.report import PriorityLevel, ReportCategory

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.department import Department
    from app.models.report import Report
    from app.models.work_order import WorkOrder


class IssueStatus(str, enum.Enum):
    """Status of aggregated civic infrastructure issue."""

    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


IssuePriority = PriorityLevel


class Issue(Base):
    """Aggregated civic issue model combining multiple citizen reports."""

    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    issue_code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[ReportCategory] = mapped_column(
        SQLEnum(ReportCategory, native_enum=False), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[IssueStatus] = mapped_column(
        SQLEnum(IssueStatus, native_enum=False), default=IssueStatus.OPEN, nullable=False, index=True
    )
    priority: Mapped[PriorityLevel] = mapped_column(
        SQLEnum(PriorityLevel, native_enum=False), default=PriorityLevel.MEDIUM, nullable=False, index=True
    )

    department_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    assigned_to_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    neighborhood: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    estimated_cost: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    actual_cost: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    total_reports_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)

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
    department: Mapped[Optional["Department"]] = relationship(
        "Department", back_populates="issues"
    )
    assigned_to: Mapped[Optional["User"]] = relationship(
        "User", back_populates="assigned_issues"
    )
    reports: Mapped[List["Report"]] = relationship("Report", back_populates="issue")
    work_orders: Mapped[List["WorkOrder"]] = relationship(
        "WorkOrder", back_populates="issue", cascade="all, delete-orphan"
    )
