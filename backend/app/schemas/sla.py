"""SLA Pydantic schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class SLARuleCreate(BaseModel):
    name: str
    priority: str
    response_hours: float
    inspection_hours: float
    assignment_hours: float
    resolution_hours: float
    category: Optional[str] = None
    department_id: Optional[int] = None
    approaching_threshold_pct: Optional[float] = 0.8

class SLARuleRead(BaseModel):
    id: int
    name: str
    priority: str
    category: Optional[str] = None
    jurisdiction_id: Optional[int] = None
    department_id: Optional[int] = None
    response_hours: float
    inspection_hours: float
    assignment_hours: float
    resolution_hours: float
    approaching_threshold_pct: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SLAStatusResponse(BaseModel):
    service_request_id: int
    sr_number: str
    sla_status: str
    response_due_at: Optional[datetime] = None
    resolution_due_at: Optional[datetime] = None
    hours_remaining_response: Optional[float] = None
    hours_remaining_resolution: Optional[float] = None
    is_breached: bool
    is_approaching: bool

class SLAEscalationLogRead(BaseModel):
    id: int
    service_request_id: int
    escalation_type: str
    escalated_to_id: Optional[int] = None
    message: str
    is_acknowledged: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
