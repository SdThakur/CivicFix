"""SLA models."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.department import Department
    # Jurisdiction model might be in another module
    from app.models.user import User
    # service_requests model is not explicitly named, maybe it is reports or issues?
    # Wait, the prompt says `service_requests` table, I'll use it as `service_requests.id`.

class SLARule(Base):
    __tablename__ = "sla_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    jurisdiction_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("jurisdictions.id", ondelete="SET NULL"), nullable=True)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    
    response_hours: Mapped[float] = mapped_column(Float, nullable=False)
    inspection_hours: Mapped[float] = mapped_column(Float, nullable=False)
    assignment_hours: Mapped[float] = mapped_column(Float, nullable=False)
    resolution_hours: Mapped[float] = mapped_column(Float, nullable=False)
    approaching_threshold_pct: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class SLAEscalationLog(Base):
    __tablename__ = "sla_escalation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    service_request_id: Mapped[int] = mapped_column(Integer, ForeignKey("service_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    escalation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    escalated_to_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
