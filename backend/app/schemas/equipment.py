"""Equipment Management schemas."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.equipment import EquipmentStatus

class EquipmentTypeRead(BaseModel):
    id: int
    name: str
    category: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class EquipmentCreate(BaseModel):
    unit_code: str
    name: str
    equipment_type_id: Optional[int] = None
    department_id: Optional[int] = None
    status: Optional[EquipmentStatus] = EquipmentStatus.AVAILABLE

class EquipmentUpdate(BaseModel):
    status: Optional[EquipmentStatus] = None
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None

class EquipmentRead(BaseModel):
    id: int
    unit_code: str
    name: str
    equipment_type_id: Optional[int] = None
    department_id: Optional[int] = None
    maintenance_zone_id: Optional[int] = None
    status: EquipmentStatus
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    home_base_lat: Optional[float] = None
    home_base_lng: Optional[float] = None
    last_maintenance_at: Optional[datetime] = None
    next_maintenance_due_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    equipment_type_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class EquipmentAssignmentCreate(BaseModel):
    equipment_id: int
    work_order_id: int
    crew_id: Optional[int] = None

class EquipmentAssignmentRead(BaseModel):
    id: int
    equipment_id: int
    work_order_id: int
    crew_id: Optional[int] = None
    assigned_by_id: Optional[int] = None
    assigned_at: datetime
    released_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
