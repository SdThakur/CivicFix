"""Pydantic v2 schemas for User management and authentication."""

from datetime import datetime
from typing import Optional, Union
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user properties."""

    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    phone_number: Optional[str] = Field(None, max_length=50)
    role: UserRole = UserRole.CITIZEN
    department_id: Optional[Union[int, uuid.UUID]] = None
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema."""

    password: str = Field(..., min_length=6, max_length=100)


class UserUpdate(BaseModel):
    """User update schema."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    phone_number: Optional[str] = Field(None, max_length=50)
    role: Optional[UserRole] = None
    department_id: Optional[Union[int, uuid.UUID]] = None
    is_active: Optional[bool] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    """User response schema."""

    id: Union[int, uuid.UUID]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """User login payload."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """Bearer token response schema."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """JWT Token payload data."""

    sub: Optional[str] = None
    role: Optional[UserRole] = None
