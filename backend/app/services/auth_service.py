"""Authentication Service handling user authentication and token creation."""

from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User
from app.repositories.user_repo import user_repo
from app.schemas.user import UserCreate, UserLogin, Token, UserResponse


class AuthService:
    """Business logic for user authentication."""

    async def register_user(self, db: AsyncSession, user_in: UserCreate) -> User:
        """Register a new user account."""
        existing = await user_repo.get_by_email(db, user_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists.",
            )

        hashed_password = get_password_hash(user_in.password)
        db_user = await user_repo.create(
            db=db, obj_in=user_in, hashed_password=hashed_password
        )
        return db_user

    async def authenticate_user(
        self, db: AsyncSession, login_data: UserLogin
    ) -> User:
        """Authenticate user credentials."""
        user = await user_repo.get_by_email(db, login_data.email)
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account.",
            )

        return user

    def create_user_token(self, user: User) -> Token:
        """Generate JWT access token for authenticated user."""
        access_token = create_access_token(
            subject=user.id, extra_claims={"email": user.email, "role": user.role.value}
        )
        user_resp = UserResponse.model_validate(user)
        return Token(access_token=access_token, token_type="bearer", user=user_resp)


auth_service = AuthService()
