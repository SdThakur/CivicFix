"""Inspection Pydantic schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.inspection import (
    InspectionStatus,
    SafetyRiskLevel,
    RepairRecommendation,
)


class InspectionCreate(BaseModel):
    service_request_id: Optional[int] = None
    issue_id: Optional[int] = None
    ai_category: Optional[str] = None
    ai_severity: Optional[str] = None
    ai_priority_score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class InspectionUpdate(BaseModel):
    status: Optional[InspectionStatus] = None
    confirmed_category: Optional[str] = None
    confirmed_severity: Optional[str] = None
    safety_risk: Optional[SafetyRiskLevel] = None
    is_emergency: Optional[bool] = None
    lanes_affected: Optional[int] = None
    estimated_area_sqm: Optional[float] = None
    depth_cm: Optional[float] = None
    road_condition_rating: Optional[int] = None
    surface_type_found: Optional[str] = None
    recommended_repair: Optional[RepairRecommendation] = None
    estimated_repair_hours: Optional[float] = None
    estimated_material_cost: Optional[float] = None
    estimated_labor_cost: Optional[float] = None
    inspection_notes: Optional[str] = None
    photo_urls: Optional[List[str]] = None
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class InspectionRead(BaseModel):
    id: int
    inspection_number: str
    service_request_id: Optional[int] = None
    issue_id: Optional[int] = None
    inspector_id: Optional[int] = None
    status: InspectionStatus

    ai_category: Optional[str] = None
    ai_severity: Optional[str] = None
    ai_priority_score: Optional[float] = None

    confirmed_category: Optional[str] = None
    confirmed_severity: Optional[str] = None
    safety_risk: SafetyRiskLevel
    is_emergency: bool
    lanes_affected: int
    estimated_area_sqm: Optional[float] = None
    depth_cm: Optional[float] = None
    road_condition_rating: Optional[int] = None
    surface_type_found: Optional[str] = None
    recommended_repair: Optional[RepairRecommendation] = None
    estimated_repair_hours: Optional[float] = None
    estimated_material_cost: Optional[float] = None
    estimated_labor_cost: Optional[float] = None
    inspection_notes: Optional[str] = None
    photo_urls: Optional[List[str]] = None

    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
