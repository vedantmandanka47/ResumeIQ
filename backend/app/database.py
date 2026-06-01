"""Async SQLAlchemy connection management."""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Create the engine lazily so missing env vars fail in startup validation."""
    global _engine
    if _engine is None:
        if not settings.database_url:
            raise RuntimeError("DATABASE_URL is not configured")
        _engine = create_async_engine(
            settings.database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a request-scoped database session."""
    async with get_session_factory()() as session:
        yield session


async def init_db() -> None:
    """Confirm database connectivity. Schema changes are managed by Alembic."""
    try:
        async with get_engine().connect() as connection:
            await connection.execute(text("SELECT 1"))
        logger.info("Database connection established successfully.")
    except Exception as exc:
        logger.critical("Cannot connect to database: %s", exc)
        raise


async def check_db_connection() -> dict[str, str]:
    try:
        async with get_engine().connect() as connection:
            await connection.execute(text("SELECT 1"))
        return {"db": "connected"}
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        return {"db": "error", "detail": str(exc)}


async def dispose_db() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
