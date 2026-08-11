"""FastAPI dependencies for Database Sessions, Authentication, and Role-Based Access Control."""

from typing import AsyncGenerator, List, Callable, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.core.config import settings
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.repositories.user_repo import user_repo

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """Validate access token and return current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise credentials_exception

    user = await user_repo.get_by_id(db, user_id=user_id)
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure current user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user account."
        )
    return current_user


def require_roles(*allowed_roles: UserRole) -> Callable[..., Any]:
    """Role-based Access Control (RBAC) dependency factory."""

    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User with role '{current_user.role.value}' does not have sufficient permission. Required: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return role_checker

def require_permission(permission: str):
    """Fine-grained permission-based access control."""
    # Define permission -> role mapping
    PERMISSION_ROLES = {
        "service_request.verify": [UserRole.DISPATCHER_311, UserRole.STAFF, UserRole.MANAGER, UserRole.SUPERVISOR, UserRole.ADMIN],
        "inspection.create": [UserRole.INSPECTOR, UserRole.STAFF, UserRole.MANAGER, UserRole.SUPERVISOR, UserRole.ADMIN],
        "work_order.assign": [UserRole.CREW_LEAD, UserRole.SUPERVISOR, UserRole.MANAGER, UserRole.DEPARTMENT_MANAGER, UserRole.ADMIN],
        "work_order.complete": [UserRole.FIELD_WORKER, UserRole.CREW_LEAD, UserRole.SUPERVISOR, UserRole.MANAGER, UserRole.ADMIN],
        "asset.edit": [UserRole.GIS_ANALYST, UserRole.MANAGER, UserRole.ADMIN],
        "gis.manage": [UserRole.GIS_ANALYST, UserRole.ADMIN],
        "analytics.view": [UserRole.MANAGER, UserRole.DEPARTMENT_MANAGER, UserRole.SUPERVISOR, UserRole.ADMIN],
        "maintenance.approve": [UserRole.SUPERVISOR, UserRole.MANAGER, UserRole.DEPARTMENT_MANAGER, UserRole.ADMIN],
    }
    async def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        allowed_roles = PERMISSION_ROLES.get(permission, [UserRole.ADMIN])
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail=f"Permission '{permission}' required.")
        return current_user
    return permission_checker
