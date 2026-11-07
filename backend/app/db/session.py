"""Database session management."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings

is_sqlite = settings.SQLALCHEMY_DATABASE_URI.startswith("sqlite")
if is_sqlite:
    connect_args = {"check_same_thread": False}
else:
    # Supabase Transaction Pooler (port 6543) requires statement_cache_size=0 with asyncpg
    connect_args = {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    }

engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
async_session_maker = AsyncSessionLocal

# ─── Read Replica Engine & Session (Supabase Read Scaling) ────────────────────
replica_url = settings.DATABASE_REPLICA_URL
if replica_url:
    is_replica_sqlite = replica_url.startswith("sqlite")
    replica_connect_args = (
        {"check_same_thread": False}
        if is_replica_sqlite
        else {"statement_cache_size": 0, "prepared_statement_cache_size": 0}
    )
    replica_engine = create_async_engine(
        replica_url,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args=replica_connect_args,
    )
    ReplicaAsyncSessionLocal = async_sessionmaker(
        bind=replica_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
else:
    replica_engine = engine
    ReplicaAsyncSessionLocal = AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for obtaining an async database session (Primary read/write)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_read_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency yielding a read-only session routed to replica when available, primary otherwise."""
    async with ReplicaAsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
