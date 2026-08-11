"""Notification repository handling data access layer for user notifications."""

from typing import List, Optional, Tuple
from sqlalchemy import select, func, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notification, NotificationType
from app.schemas.notification import NotificationCreate


class NotificationRepository:
    """Async repository for Notification database operations."""

    async def get_by_id(
        self, db: AsyncSession, notification_id: int
    ) -> Optional[Notification]:
        """Fetch notification by ID."""
        result = await db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalars().first()

    async def get_user_notifications(
        self,
        db: AsyncSession,
        user_id: int,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Notification], int]:
        """Fetch paginated notifications for a user with unread filter and total count."""
        query = select(Notification).where(Notification.user_id == user_id)
        count_query = select(func.count(Notification.id)).where(
            Notification.user_id == user_id
        )

        if unread_only:
            query = query.where(Notification.is_read == False)
            count_query = count_query.where(Notification.is_read == False)

        count_res = await db.execute(count_query)
        total = count_res.scalar() or 0

        query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        notifications = list(result.scalars().all())
        return notifications, total

    async def create(
        self, db: AsyncSession, obj_in: NotificationCreate
    ) -> Notification:
        """Create a new notification record."""
        db_obj = Notification(
            user_id=obj_in.user_id,
            title=obj_in.title,
            message=obj_in.message,
            type=obj_in.type,
            reference_id=obj_in.reference_id,
            reference_type=obj_in.reference_type,
            is_read=False,
        )
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def mark_as_read(
        self, db: AsyncSession, notification_id: int, user_id: int
    ) -> Optional[Notification]:
        """Mark a specific notification as read."""
        notification = await self.get_by_id(db, notification_id)
        if notification and notification.user_id == user_id:
            notification.is_read = True
            db.add(notification)
            await db.flush()
            await db.refresh(notification)
            return notification
        return None

    async def mark_all_read(self, db: AsyncSession, user_id: int) -> int:
        """Mark all notifications as read for a given user."""
        stmt = (
            update(Notification)
            .where(
                and_(Notification.user_id == user_id, Notification.is_read == False)
            )
            .values(is_read=True)
        )
        result = await db.execute(stmt)
        return result.rowcount


notification_repo = NotificationRepository()
