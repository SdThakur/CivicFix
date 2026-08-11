"""Pydantic v2 schemas for authentication operations."""

from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Token(BaseModel):
    """JWT Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """JWT Token payload contents."""
    sub: Optional[str] = None
    role: Optional[str] = None
    type: Optional[str] = None
    exp: Optional[int] = None
    iat: Optional[int] = None


class LoginRequest(BaseModel):
    """User login request schema."""
    email: EmailStr
    password: str = Field(..., min_length=6)


class RefreshTokenRequest(BaseModel):
    """Token refresh request schema."""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Password reset request initiation schema."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    token: str
    new_password: str = Field(..., min_length=8)
