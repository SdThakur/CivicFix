"""Report database model and enums."""

from datetime import datetime, timezone
import enum
from typing import TYPE_CHECKING, List, Optional, Union, Dict, Any
import uuid
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


class ReportCategory(str, enum.Enum):
    """Categories of civic infrastructure reports."""

    POTHOLE = "POTHOLE"
    STREETLIGHT = "STREETLIGHT"
    WATER_LEAK = "WATER_LEAK"
    GRAFFITI = "GRAFFITI"
    TRASH = "TRASH"
    PARK_DAMAGE = "PARK_DAMAGE"
    TRAFFIC_SIGNAL = "TRAFFIC_SIGNAL"
    OTHER = "OTHER"


class ReportStatus(str, enum.Enum):
    """Lifecycle status of a report."""

    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    DUPLICATE = "DUPLICATE"


class PriorityLevel(str, enum.Enum):
    """Priority levels for issues and reports."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


ReportPriority = PriorityLevel


class Report(Base):
    """Citizen infrastructure report representation."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tracking_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[ReportCategory] = mapped_column(
        SQLEnum(ReportCategory, native_enum=False), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ReportStatus] = mapped_column(
        SQLEnum(ReportStatus, native_enum=False),
        default=ReportStatus.SUBMITTED,
        nullable=False,
        index=True,
    )
    priority: Mapped[PriorityLevel] = mapped_column(
        SQLEnum(PriorityLevel, native_enum=False),
        default=PriorityLevel.MEDIUM,
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    latitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    neighborhood: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    image_urls: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list, nullable=True)

    issue_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("issues.id", ondelete="SET NULL"), nullable=True, index=True
    )

    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    duplicate_of_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("reports.id", ondelete="SET NULL"), nullable=True
    )

    ai_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    upvotes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

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
    user: Mapped["User"] = relationship("User", back_populates="reports")
    issue: Mapped[Optional["Issue"]] = relationship("Issue", back_populates="reports")
