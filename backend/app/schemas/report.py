"""Pydantic v2 schemas for Report handling."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.report import PriorityLevel, ReportCategory, ReportStatus, ReportPriority


class LocationCreate(BaseModel):
    """Location payload."""

    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    address: Optional[str] = ""
    neighborhood: Optional[str] = ""


class LocationResponse(LocationCreate):
    """Location response."""

    id: Optional[Union[int, uuid.UUID]] = None

    model_config = ConfigDict(from_attributes=True)


class ReportBase(BaseModel):
    """Base Report schema."""

    title: str = Field(..., min_length=3, max_length=255)
    category: ReportCategory
    description: str = Field(..., min_length=5)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    address: str
    neighborhood: str
    image_urls: List[str] = Field(default_factory=list)


class ReportCreate(BaseModel):
    """Report creation schema allowing flat coordinates or nested location."""

    title: str = Field(..., min_length=3, max_length=255)
    category: ReportCategory
    description: str = Field(...)
    latitude: float = Field(default=0.0, ge=-90.0, le=90.0)
    longitude: float = Field(default=0.0, ge=-180.0, le=180.0)
    address: str = ""
    neighborhood: str = ""
    image_urls: List[str] = Field(default_factory=list)
    location: Optional[LocationCreate] = None

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, v: Any) -> ReportCategory:
        if isinstance(v, str):
            val = v.upper().strip()
            if val in ("GENERAL", "INCIDENT", "UNKNOWN", "OTHER"):
                return ReportCategory.OTHER
            try:
                return ReportCategory(val)
            except ValueError:
                return ReportCategory.OTHER
        return v

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, v: Any) -> str:
        if not v or not isinstance(v, str):
            return "Infrastructure issue reported."
        v_str = v.strip()
        if len(v_str) < 5:
            return f"{v_str} (Reported issue details)"
        return v_str

    def model_post_init(self, __context: Any) -> None:
        if self.location:
            if self.latitude == 0.0:
                self.latitude = self.location.latitude
            if self.longitude == 0.0:
                self.longitude = self.location.longitude
            if not self.address and self.location.address:
                self.address = self.location.address
            if not self.neighborhood and self.location.neighborhood:
                self.neighborhood = self.location.neighborhood


class ReportUpdate(BaseModel):
    """Report status/details update schema."""

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ReportStatus] = None
    priority: Optional[PriorityLevel] = None
    issue_id: Optional[Union[int, uuid.UUID]] = None
    is_duplicate: Optional[bool] = None
    duplicate_of_id: Optional[Union[int, uuid.UUID]] = None


class PriorityScoreBreakdown(BaseModel):
    """Breakdown of calculated priority score components."""

    category_weight: float
    age_boost: float
    upvote_boost: float
    duplicate_cluster_boost: float
    final_score: float
    calculated_priority: PriorityLevel


class ReportResponse(ReportBase):
    """Report response DTO."""

    id: Union[int, uuid.UUID]
    tracking_number: str
    status: ReportStatus
    priority: PriorityLevel
    user_id: Union[int, uuid.UUID]
    issue_id: Optional[Union[int, uuid.UUID]] = None
    is_duplicate: bool = False
    duplicate_of_id: Optional[Union[int, uuid.UUID]] = None
    ai_score: float = 0.0
    upvotes: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportFilter(BaseModel):
    """Filter parameter parameters for querying reports."""

    status: Optional[ReportStatus] = None
    category: Optional[ReportCategory] = None
    priority: Optional[PriorityLevel] = None
    neighborhood: Optional[str] = None
    user_id: Optional[Union[int, uuid.UUID]] = None
    is_duplicate: Optional[bool] = None
    skip: int = 0
    limit: int = 50
