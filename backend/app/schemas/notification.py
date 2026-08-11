"""Pydantic v2 schemas for Notifications."""

from datetime import datetime
from typing import Optional, Union
import uuid
from pydantic import BaseModel, ConfigDict
from app.models.notification import NotificationType


class NotificationBase(BaseModel):
    """Base notification schema."""

    title: str
    message: str
    type: NotificationType = NotificationType.SYSTEM
    reference_id: Optional[Union[int, uuid.UUID]] = None
    reference_type: Optional[str] = None


class NotificationCreate(NotificationBase):
    """Notification creation schema."""

    user_id: Union[int, uuid.UUID]


class NotificationResponse(NotificationBase):
    """Notification response schema."""

    id: Union[int, uuid.UUID]
    user_id: Union[int, uuid.UUID]
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
