"""User database model."""

from datetime import datetime, timezone
import enum
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.report import Report
    from app.models.issue import Issue
    from app.models.work_order import WorkOrder
    from app.models.notification import Notification


class UserRole(str, enum.Enum):
    """User authorization roles."""

    CITIZEN = "CITIZEN"
    STAFF = "STAFF"
    MANAGER = "MANAGER"
    SUPERVISOR = "SUPERVISOR"
    CONTRACTOR = "CONTRACTOR"
    ADMIN = "ADMIN"
    DISPATCHER_311 = "DISPATCHER_311"
    INSPECTOR = "INSPECTOR"
    FIELD_WORKER = "FIELD_WORKER"
    CREW_LEAD = "CREW_LEAD"
    DEPARTMENT_MANAGER = "DEPARTMENT_MANAGER"
    GIS_ANALYST = "GIS_ANALYST"


class User(Base):
    """User entity representation."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, native_enum=False), default=UserRole.CITIZEN, nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    department_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
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
    department: Mapped[Optional["Department"]] = relationship(
        "Department", back_populates="users"
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report", back_populates="user", cascade="all, delete-orphan"
    )
    assigned_issues: Mapped[List["Issue"]] = relationship(
        "Issue", back_populates="assigned_to"
    )
    assigned_work_orders: Mapped[List["WorkOrder"]] = relationship(
        "WorkOrder", back_populates="assigned_to"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
