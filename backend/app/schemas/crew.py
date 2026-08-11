"""Crew Management schemas."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.crew import CrewStatus

class SkillRead(BaseModel):
    id: int
    name: str
    category: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class CrewCreate(BaseModel):
    name: str
    crew_code: str
    department_id: Optional[int] = None
    supervisor_id: Optional[int] = None
    maintenance_zone_id: Optional[int] = None
    home_base_lat: Optional[float] = None
    home_base_lng: Optional[float] = None
    max_concurrent_jobs: Optional[int] = 3

class CrewUpdate(BaseModel):
    name: Optional[str] = None
    crew_code: Optional[str] = None
    department_id: Optional[int] = None
    supervisor_id: Optional[int] = None
    maintenance_zone_id: Optional[int] = None
    status: Optional[CrewStatus] = None
    home_base_lat: Optional[float] = None
    home_base_lng: Optional[float] = None
    home_base_address: Optional[str] = None
    max_concurrent_jobs: Optional[int] = None
    notes: Optional[str] = None

class CrewMemberAdd(BaseModel):
    user_id: int
    is_lead: Optional[bool] = False

class CrewMemberInfo(BaseModel):
    id: int
    user_id: int
    is_lead: bool
    joined_at: datetime
    is_active: bool
    # To handle basic user details, assuming user relation is loaded
    # Optional fields if we extract them from the user model
    name: Optional[str] = None
    email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class CrewRead(BaseModel):
    id: int
    name: str
    crew_code: str
    department_id: Optional[int] = None
    supervisor_id: Optional[int] = None
    maintenance_zone_id: Optional[int] = None
    status: CrewStatus
    home_base_lat: Optional[float] = None
    home_base_lng: Optional[float] = None
    home_base_address: Optional[str] = None
    max_concurrent_jobs: int
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    members: List[CrewMemberInfo] = []
    active_work_order_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

class EmployeeSkillCreate(BaseModel):
    skill_id: int
    proficiency_level: Optional[int] = 1
    certified: Optional[bool] = False
