"""Preventive maintenance schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.preventive_maintenance import MaintenanceRecommendationStatus, MaintenanceType


class MaintenanceRecommendationBase(BaseModel):
    """Shared properties for preventive maintenance recommendation."""
    road_segment_id: Optional[int] = None
    asset_id: Optional[int] = None
    road_id: Optional[int] = None
    maintenance_type: MaintenanceType
    title: str
    reasoning: str
    risk_score_at_creation: float
    incident_count_trigger: int
    estimated_cost: Optional[float] = None


class MaintenanceRecommendationCreate(MaintenanceRecommendationBase):
    """Properties to receive on creation."""
    pass


class MaintenanceRecommendationApprove(BaseModel):
    """Properties to receive on approval."""
    approved_by_id: int
    scheduled_start: Optional[datetime] = None
    notes: Optional[str] = None


class MaintenanceRecommendationReject(BaseModel):
    """Properties to receive on rejection."""
    rejection_reason: str


class MaintenanceRecommendationRead(MaintenanceRecommendationBase):
    """Properties to return to client."""
    id: int
    rec_number: str
    status: MaintenanceRecommendationStatus
    days_since_last_maintenance: Optional[int] = None
    priority: str
    recommended_by: str
    approved_by_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    scheduled_work_order_id: Optional[int] = None
    due_by: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
