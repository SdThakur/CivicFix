"""Equipment Management models."""

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Boolean, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.work_order import WorkOrder
    from app.models.crew import Crew
    from app.models.user import User

class EquipmentStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    IN_USE = "IN_USE"
    MAINTENANCE = "MAINTENANCE"
    DECOMMISSIONED = "DECOMMISSIONED"

class EquipmentType(Base):
    __tablename__ = "equipment_types"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    required_skills: Mapped[Optional[List[int]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

class Equipment(Base):
    __tablename__ = "equipment_items"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    unit_code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    equipment_type_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("equipment_types.id", ondelete="SET NULL"), nullable=True)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    maintenance_zone_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("maintenance_zones.id", ondelete="SET NULL"), nullable=True)
    
    status: Mapped[EquipmentStatus] = mapped_column(SQLEnum(EquipmentStatus, native_enum=False), default=EquipmentStatus.AVAILABLE, nullable=False)
    current_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    home_base_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    home_base_lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    last_maintenance_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_maintenance_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    equipment_type: Mapped[Optional["EquipmentType"]] = relationship("EquipmentType")
    department: Mapped[Optional["Department"]] = relationship("Department")

class EquipmentAssignment(Base):
    __tablename__ = "equipment_assignments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    equipment_id: Mapped[int] = mapped_column(Integer, ForeignKey("equipment_items.id", ondelete="CASCADE"), index=True, nullable=False)
    work_order_id: Mapped[int] = mapped_column(Integer, ForeignKey("work_orders.id", ondelete="CASCADE"), index=True, nullable=False)
    crew_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("crews.id", ondelete="SET NULL"), nullable=True)
    assigned_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    released_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    equipment: Mapped["Equipment"] = relationship("Equipment")
    work_order: Mapped["WorkOrder"] = relationship("WorkOrder")
    crew: Mapped[Optional["Crew"]] = relationship("Crew")
    assigned_by: Mapped[Optional["User"]] = relationship("User")
