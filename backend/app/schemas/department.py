"""Pydantic v2 schemas for Department management."""

from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class DepartmentBase(BaseModel):
    """Base department properties."""
    name: str = Field(..., min_length=2, max_length=255)
    code: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    is_active: bool = True


class DepartmentCreate(DepartmentBase):
    """Department creation schema."""
    pass


class DepartmentUpdate(BaseModel):
    """Department update schema."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    """Department response schema."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
