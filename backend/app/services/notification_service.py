"""Notification Service handling dispatching and reading of system notifications."""

from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notification, NotificationType
from app.repositories.notification_repo import notification_repo
from app.schemas.notification import NotificationCreate


class NotificationService:
    """Business logic for system notifications."""

    async def send_notification(
        self,
        db: AsyncSession,
        user_id: int,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.SYSTEM,
        reference_id: Optional[int] = None,
        reference_type: Optional[str] = None,
    ) -> Notification:
        """Create and send a notification to a specific user."""
        notif_in = NotificationCreate(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            reference_id=reference_id,
            reference_type=reference_type,
        )
        return await notification_repo.create(db=db, obj_in=notif_in)

    async def get_user_notifications(
        self,
        db: AsyncSession,
        user_id: int,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Notification], int]:
        """Fetch user notifications."""
        return await notification_repo.get_user_notifications(
            db=db, user_id=user_id, unread_only=unread_only, skip=skip, limit=limit
        )

    async def mark_read(
        self, db: AsyncSession, notification_id: int, user_id: int
    ) -> Optional[Notification]:
        """Mark notification as read."""
        return await notification_repo.mark_as_read(
            db=db, notification_id=notification_id, user_id=user_id
        )

    async def mark_all_read(self, db: AsyncSession, user_id: int) -> int:
        """Mark all notifications as read."""
        return await notification_repo.mark_all_read(db=db, user_id=user_id)


notification_service = NotificationService()
