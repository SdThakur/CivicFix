"""Pytest configuration and async test fixtures for CivicFix backend."""

from typing import AsyncGenerator
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.models import Base
from app.db.session import get_db as session_get_db
from app.api.deps import get_db as deps_get_db
from app.core.security import get_password_hash, create_access_token
from app.main import app
from app.models.user import User, UserRole
from app.models.department import Department

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_civicfix.db"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create tables, yield clean session, and drop tables per test function."""
    async with test_engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.drop_all(sync_conn, checkfirst=True))
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, checkfirst=True))

    async with TestAsyncSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.drop_all(sync_conn, checkfirst=True))


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Return HTTPX AsyncClient with database session dependency overridden."""

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[session_get_db] = _override_get_db
    app.dependency_overrides[deps_get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def sample_department(db_session: AsyncSession) -> Department:
    """Create sample Public Works department."""
    dept = Department(
        name="Department of Public Works",
        code="DPW",
        description="Public infrastructure and road maintenance",
        contact_email="dpw@civicfix.gov",
    )
    db_session.add(dept)
    await db_session.flush()
    await db_session.refresh(dept)
    return dept


@pytest.fixture
async def citizen_user(db_session: AsyncSession) -> User:
    """Create citizen user fixture."""
    user = User(
        email="citizen@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Jane Citizen",
        role=UserRole.CITIZEN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def staff_user(db_session: AsyncSession, sample_department: Department) -> User:
    """Create municipal staff user fixture."""
    user = User(
        email="staff@civicfix.gov",
        hashed_password=get_password_hash("password123"),
        full_name="Bob Staff",
        role=UserRole.STAFF,
        is_active=True,
        department_id=sample_department.id,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_user(db_session: AsyncSession, sample_department: Department) -> User:
    """Create admin user fixture."""
    user = User(
        email="admin@civicfix.gov",
        hashed_password=get_password_hash("password123"),
        full_name="Alice Admin",
        role=UserRole.ADMIN,
        is_active=True,
        department_id=sample_department.id,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
def citizen_token_headers(citizen_user: User) -> dict:
    """Auth headers for citizen user."""
    token = create_access_token(
        subject=citizen_user.id,
        role=citizen_user.role.value,
        extra_claims={"email": citizen_user.email, "role": citizen_user.role.value},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def staff_token_headers(staff_user: User) -> dict:
    """Auth headers for staff user."""
    token = create_access_token(
        subject=staff_user.id,
        role=staff_user.role.value,
        extra_claims={"email": staff_user.email, "role": staff_user.role.value},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_token_headers(admin_user: User) -> dict:
    """Auth headers for admin user."""
    token = create_access_token(
        subject=admin_user.id,
        role=admin_user.role.value,
        extra_claims={"email": admin_user.email, "role": admin_user.role.value},
    )
    return {"Authorization": f"Bearer {token}"}
