"""Pydantic v2 schemas for Work Orders."""

from datetime import datetime
from typing import Optional, Union
import uuid
from pydantic import BaseModel, ConfigDict, Field
from app.models.report import PriorityLevel
from app.models.work_order import WorkOrderStatus


class WorkOrderBase(BaseModel):
    """Base Work Order schema."""

    issue_id: Optional[Union[int, uuid.UUID]] = None
    title: str = Field(..., min_length=3, max_length=255)
    description: str
    priority: PriorityLevel = PriorityLevel.MEDIUM
    assigned_department_id: Optional[Union[int, uuid.UUID]] = None
    assigned_to_id: Optional[Union[int, uuid.UUID]] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    estimated_hours: Optional[float] = 0.0
    notes: Optional[str] = None


class WorkOrderCreate(WorkOrderBase):
    """Work Order creation schema."""

    pass


class WorkOrderUpdate(BaseModel):
    """Work Order update schema."""

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[WorkOrderStatus] = None
    priority: Optional[PriorityLevel] = None
    assigned_department_id: Optional[Union[int, uuid.UUID]] = None
    assigned_to_id: Optional[Union[int, uuid.UUID]] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    notes: Optional[str] = None
    before_photo_url: Optional[str] = None
    after_photo_url: Optional[str] = None
    blocked_reason: Optional[str] = None
    blocked_notes: Optional[str] = None


class WorkOrderResponse(WorkOrderBase):
    """Work Order response DTO."""

    id: Union[int, uuid.UUID]
    work_order_number: str
    status: WorkOrderStatus
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    actual_hours: Optional[float] = 0.0
    before_photo_url: Optional[str] = None
    after_photo_url: Optional[str] = None
    blocked_reason: Optional[str] = None
    blocked_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkOrderReportBlocked(BaseModel):
    """Schema for reporting a blocked work order."""
    reason: str
    notes: Optional[str] = None
    photo_url: Optional[str] = None
