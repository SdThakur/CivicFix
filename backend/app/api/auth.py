"""Authentication API Router."""

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, Token, UserResponse
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    user_in: UserCreate, db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Register a new citizen or municipal user."""
    user = await auth_service.register_user(db=db, user_in=user_in)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin, db: AsyncSession = Depends(get_db)
) -> Token:
    """Authenticate via JSON credentials."""
    user = await auth_service.authenticate_user(db=db, login_data=login_data)
    return auth_service.create_user_token(user)


@router.post("/login/form", response_model=Token)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """OAuth2 password form login endpoint for Swagger UI compatibility."""
    login_data = UserLogin(email=form_data.username, password=form_data.password)
    user = await auth_service.authenticate_user(db=db, login_data=login_data)
    return auth_service.create_user_token(user)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Get current authenticated user profile."""
    return UserResponse.model_validate(current_user)
