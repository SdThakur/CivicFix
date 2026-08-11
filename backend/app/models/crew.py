"""Crew Management models."""

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Boolean, Text, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.user import User
    from app.models.work_order import WorkOrder

class CrewStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ON_LEAVE = "ON_LEAVE"

class Skill(Base):
    __tablename__ = "skills"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

class Crew(Base):
    __tablename__ = "crews"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    crew_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    supervisor_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    maintenance_zone_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("maintenance_zones.id", ondelete="SET NULL"), nullable=True)
    
    status: Mapped[CrewStatus] = mapped_column(SQLEnum(CrewStatus, native_enum=False), default=CrewStatus.ACTIVE, nullable=False)
    home_base_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    home_base_lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    home_base_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    max_concurrent_jobs: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    department: Mapped[Optional["Department"]] = relationship("Department")
    supervisor: Mapped[Optional["User"]] = relationship("User")
    members: Mapped[List["CrewMember"]] = relationship("CrewMember", back_populates="crew", cascade="all, delete-orphan")
    work_orders: Mapped[List["WorkOrder"]] = relationship("WorkOrder", back_populates="crew")

class CrewMember(Base):
    __tablename__ = "crew_members"
    __table_args__ = (UniqueConstraint("crew_id", "user_id", name="uix_crew_members_crew_user"),)
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    crew_id: Mapped[int] = mapped_column(Integer, ForeignKey("crews.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    
    is_lead: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    left_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    crew: Mapped["Crew"] = relationship("Crew", back_populates="members")
    user: Mapped["User"] = relationship("User")

class EmployeeSkill(Base):
    __tablename__ = "employee_skills"
    __table_args__ = (UniqueConstraint("user_id", "skill_id", name="uix_employee_skills_user_skill"),)
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), index=True, nullable=False)
    
    proficiency_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    certified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    certification_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    user: Mapped["User"] = relationship("User")
    skill: Mapped["Skill"] = relationship("Skill")
