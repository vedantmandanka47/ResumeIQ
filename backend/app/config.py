"""
ResumeIQ — Application Configuration
Loads and validates all environment variables at import time.
If a required variable is missing the app REFUSES to start with a clear error
message naming the missing variable (Rule 6).
"""

import os
import sys
from functools import lru_cache
from typing import List

from pydantic import field_validator, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Single source of truth for all configuration values.
    pydantic-settings reads from the .env file automatically.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",          # silently ignore unrecognised keys in .env
    )

    # ---- Application -------------------------------------------
    app_env: str = "development"
    app_version: str = "0.1.0"
    secret_key: str

    # ---- PostgreSQL --------------------------------------------
    database_url: str             # asyncpg DSN  — used at runtime
    database_url_sync: str        # psycopg2 DSN — used by Alembic

    # ---- Google / Gemini ---------------------------------------
    google_api_key: str
    gemini_model: str = "gemini-2.0-flash-exp"
    google_cloud_project: str = ""
    google_cloud_region: str = "us-central1"
    google_application_credentials: str = ""

    # ---- Google Cloud Agent Builder ----------------------------
    agent_builder_agent_name: str = ""

    # ---- MongoDB MCP Server ------------------------------------
    mongodb_uri: str
    mongodb_database: str = "resumeiq"
    mcp_server_url: str = ""
    mcp_api_key: str = ""

    # ---- Google Drive ------------------------------------------
    google_drive_client_id: str = ""
    google_drive_client_secret: str = ""
    google_drive_redirect_uri: str = "http://localhost:8000/auth/google/callback"

    # ---- Rate Limiting -----------------------------------------
    rate_limit_requests: int = 10
    rate_limit_window_seconds: int = 3600

    # ---- File Upload -------------------------------------------
    max_file_size_mb: int = 5
    allowed_extensions: str = "pdf,docx"

    # ---- CORS --------------------------------------------------
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # ---- Derived helpers ---------------------------------------
    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [e.strip().lower() for e in self.allowed_extensions.split(",") if e.strip()]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @field_validator("app_env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"app_env must be one of {allowed}, got '{v}'")
        return v


def _load_settings() -> Settings:
    """
    Load settings and produce a human-readable error on missing variables.
    The app will refuse to start — no cryptic tracebacks.
    """
    try:
        return Settings()  # type: ignore[call-arg]
    except ValidationError as exc:
        missing = []
        for error in exc.errors():
            field = " → ".join(str(loc) for loc in error["loc"])
            missing.append(f"  • {field.upper()}: {error['msg']}")
        print(
            "\n[ResumeIQ] ❌  STARTUP FAILED — Missing or invalid environment variables:\n"
            + "\n".join(missing)
            + "\n\nCopy .env.example → .env and fill in the required values.\n",
            file=sys.stderr,
        )
        sys.exit(1)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached singleton — call this everywhere instead of reading env directly."""
    return _load_settings()
