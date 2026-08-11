"""Service Request Pydantic schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.service_request import ServiceRequestStatus


class ServiceRequestStatusHistoryRead(BaseModel):
    id: int
    service_request_id: int
    from_status: Optional[str] = None
    to_status: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ServiceRequestCreate(BaseModel):
    issue_id: int
    reported_by_id: Optional[int] = None
    department_id: Optional[int] = None
    citizen_facing_summary: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ServiceRequestUpdate(BaseModel):
    status: Optional[ServiceRequestStatus] = None
    citizen_facing_summary: Optional[str] = None
    internal_notes: Optional[str] = None
    assigned_to_id: Optional[int] = None
    department_id: Optional[int] = None
    priority_override: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ServiceRequestRead(BaseModel):
    id: int
    sr_number: str
    issue_id: int
    reported_by_id: Optional[int] = None
    assigned_to_id: Optional[int] = None
    department_id: Optional[int] = None
    status: ServiceRequestStatus
    citizen_facing_summary: Optional[str] = None
    internal_notes: Optional[str] = None
    priority_override: Optional[str] = None

    acknowledged_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    assigned_at: Optional[datetime] = None
    inspection_scheduled_at: Optional[datetime] = None
    work_started_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    sla_response_due_at: Optional[datetime] = None
    sla_resolution_due_at: Optional[datetime] = None
    sla_status: str

    created_at: datetime
    updated_at: datetime

    status_history: List[ServiceRequestStatusHistoryRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
