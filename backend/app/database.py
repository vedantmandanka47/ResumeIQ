"""
ResumeIQ — PostgreSQL Database Connection Module
Uses SQLAlchemy 2.x async engine + asyncpg driver.
All DB operations in the project go through the session factory here.
"""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from app.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """
    Shared declarative base for all SQLAlchemy models.
    Import this in every models file and inherit from it.
    """
    pass


# ---------- Engine & Session Factory ----------------------------------------

def _build_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=(settings.app_env == "development"),   # log SQL in dev only
        pool_pre_ping=True,                          # detect stale connections
        pool_size=10,
        max_overflow=20,
    )


# Module-level singletons created once at import time
engine: AsyncEngine = _build_engine()

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,   # allow attribute access after commit
    autoflush=False,
    autocommit=False,
)


# ---------- FastAPI Dependency ----------------------------------------------

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields an async DB session for use as a FastAPI dependency.
    Rolls back on exception and always closes the session.

    Usage:
        @app.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------- Health Check Helper ---------------------------------------------

async def check_db_connection() -> dict:
    """
    Runs a minimal SELECT 1 query to verify the DB is reachable.
    Returns a dict suitable for the /health/db endpoint.
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        logger.info("Database health check: OK")
        return {"db": "connected"}
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        return {"db": "error", "detail": str(exc)}


# ---------- Table Initialisation (dev helper) --------------------------------

async def init_db() -> None:
    """
    Creates all tables that exist in the metadata.
    Used in development; production should use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialised.")
