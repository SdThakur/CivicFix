"""Pydantic v2 schemas for Issue management."""

from datetime import datetime
from typing import List, Optional, Union
import uuid
from pydantic import BaseModel, ConfigDict, Field
from app.models.issue import IssueStatus
from app.models.report import PriorityLevel, ReportCategory


class IssueBase(BaseModel):
    """Base Issue schema."""

    title: str = Field(..., min_length=3, max_length=255)
    category: ReportCategory
    description: str
    latitude: float
    longitude: float
    address: str
    neighborhood: str


class IssueCreate(IssueBase):
    """Issue creation schema."""

    department_id: Optional[Union[int, uuid.UUID]] = None
    assigned_to_id: Optional[Union[int, uuid.UUID]] = None
    priority: Optional[PriorityLevel] = PriorityLevel.MEDIUM
    estimated_cost: Optional[float] = 0.0


class IssueUpdate(BaseModel):
    """Issue modification schema."""

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[IssueStatus] = None
    priority: Optional[PriorityLevel] = None
    department_id: Optional[Union[int, uuid.UUID]] = None
    assigned_to_id: Optional[Union[int, uuid.UUID]] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None


class IssueResponse(IssueBase):
    """Issue response DTO."""

    id: Union[int, uuid.UUID]
    issue_code: str
    status: IssueStatus
    priority: PriorityLevel
    department_id: Optional[Union[int, uuid.UUID]] = None
    assigned_to_id: Optional[Union[int, uuid.UUID]] = None
    estimated_cost: Optional[float] = 0.0
    actual_cost: Optional[float] = 0.0
    total_reports_count: int = 1
    score: float = 50.0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
