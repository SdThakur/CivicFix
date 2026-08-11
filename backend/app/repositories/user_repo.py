"""User repository handling data access layer for User entity."""

from typing import List, Optional, Union, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
    """Async repository for User database operations."""

    async def get_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """Fetch user by primary key ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Fetch user by unique email address."""
        result = await db.execute(
            select(User).where(func.lower(User.email) == func.lower(email))
        )
        return result.scalars().first()

    async def get_multi(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None,
        department_id: Optional[int] = None,
    ) -> List[User]:
        """Get paginated list of users with optional filtering."""
        query = select(User)
        if role:
            query = query.where(User.role == role)
        if department_id:
            query = query.where(User.department_id == department_id)
        query = query.offset(skip).limit(limit).order_by(User.id.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create(
        self, db: AsyncSession, obj_in: UserCreate, hashed_password: str
    ) -> User:
        """Create a new user record."""
        phone_val = obj_in.phone or getattr(obj_in, 'phone_number', None)
        db_obj = User(
            email=obj_in.email.lower(),
            hashed_password=hashed_password,
            full_name=obj_in.full_name,
            role=obj_in.role,
            department_id=obj_in.department_id,
            phone=phone_val,
            phone_number=phone_val,
            avatar_url=obj_in.avatar_url,
        )
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        """Update an existing user record."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field) and value is not None:
                setattr(db_obj, field, value)

        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, user_id: int) -> bool:
        """Soft/hard delete a user by ID."""
        user = await self.get_by_id(db, user_id)
        if not user:
            return False
        await db.delete(user)
        await db.flush()
        return True


user_repo = UserRepository()
