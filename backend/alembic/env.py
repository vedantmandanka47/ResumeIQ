"""
Alembic environment configuration for ResumeIQ.
Reads DATABASE_URL_SYNC from .env so no credentials live in alembic.ini.
Imports all models so autogenerate detects all table changes.
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool
from dotenv import load_dotenv

# ---- Ensure the backend/app package is importable --------------------------
# Alembic runs from backend/, so we add its parent to sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# ---- Load .env so DATABASE_URL_SYNC is available ---------------------------
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

# ---- Import all models so autogenerate sees them ---------------------------
# noqa: F401 — imported for side-effect (populates Base.metadata)
from app.models import Base  # noqa: F401,E402

# ---- Alembic Config object -------------------------------------------------
config = context.config

# Override sqlalchemy.url with the sync URL from the environment.
# This keeps credentials out of alembic.ini entirely.
database_url_sync = os.environ.get("DATABASE_URL_SYNC")
if not database_url_sync:
    raise RuntimeError(
        "DATABASE_URL_SYNC is not set. "
        "Copy .env.example → .env and fill in the value."
    )
config.set_main_option("sqlalchemy.url", database_url_sync)

# ---- Logging ---------------------------------------------------------------
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---- Target metadata for autogenerate --------------------------------------
target_metadata = Base.metadata


# ---- Migration runners -----------------------------------------------------

def run_migrations_offline() -> None:
    """
    Emit migration SQL to stdout without a live DB connection.
    Used for generating SQL scripts for manual review.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,           # detect column type changes
        compare_server_default=True, # detect server default changes
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations against a live database connection.
    Uses psycopg2 (sync) — asyncpg doesn't work with Alembic.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # no pooling for migration runs
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
