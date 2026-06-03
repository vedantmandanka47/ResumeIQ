"""Environment-backed application configuration."""

import logging
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(_BACKEND_DIR / ".env")
load_dotenv(_BACKEND_DIR.parent / ".env")

REQUIRED_ENV_VARS = (
    "DATABASE_URL",
    "GOOGLE_API_KEY",
)

OPTIONAL_INTEGRATION_ENV_VARS = (
    "MONGODB_MCP_SERVER_URL",
    "MONGODB_ATLAS_URI",
    "GOOGLE_DRIVE_CLIENT_ID",
    "GOOGLE_DRIVE_CLIENT_SECRET",
    "GOOGLE_DRIVE_REFRESH_TOKEN",
)


def validate_env() -> None:
    """Fail startup with an explicit list of missing required settings."""
    missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
    if missing:
        for name in missing:
            logger.critical("Missing required environment variable: %s", name)
        raise RuntimeError(
            "Server cannot start. Missing required env vars: "
            f"{', '.join(missing)}. Copy backend/.env.example to backend/.env and fill in values."
        )

    for name in OPTIONAL_INTEGRATION_ENV_VARS:
        if not os.environ.get(name):
            logger.warning(
                "Optional integration not configured: %s (related API routes may return errors)",
                name,
            )


@dataclass(frozen=True)
class Settings:
    database_url: str = field(default_factory=lambda: os.environ.get("DATABASE_URL", ""))
    google_api_key: str = field(default_factory=lambda: os.environ.get("GOOGLE_API_KEY", ""))
    google_cloud_project: str = field(
        default_factory=lambda: os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    )
    google_cloud_location: str = field(
        default_factory=lambda: os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    )
    mongodb_mcp_server_url: str = field(
        default_factory=lambda: os.environ.get("MONGODB_MCP_SERVER_URL", "")
    )
    mongodb_atlas_uri: str = field(
        default_factory=lambda: os.environ.get("MONGODB_ATLAS_URI", "")
    )
    mongodb_database: str = field(
        default_factory=lambda: os.environ.get("MONGODB_DATABASE", "resumeiq")
    )
    mongodb_collection: str = field(
        default_factory=lambda: os.environ.get("MONGODB_COLLECTION", "analyses")
    )
    google_drive_client_id: str = field(
        default_factory=lambda: os.environ.get("GOOGLE_DRIVE_CLIENT_ID", "")
    )
    google_drive_client_secret: str = field(
        default_factory=lambda: os.environ.get("GOOGLE_DRIVE_CLIENT_SECRET", "")
    )
    google_drive_refresh_token: str = field(
        default_factory=lambda: os.environ.get("GOOGLE_DRIVE_REFRESH_TOKEN", "")
    )
    rate_limit_post: str = field(
        default_factory=lambda: os.environ.get("RATE_LIMIT_POST", "10/hour")
    )
    app_version: str = field(default_factory=lambda: os.environ.get("APP_VERSION", "0.1.0"))
    max_file_size_mb: int = field(
        default_factory=lambda: int(os.environ.get("MAX_FILE_SIZE_MB", "5"))
    )
    generated_file_ttl_hours: int = field(
        default_factory=lambda: int(os.environ.get("GENERATED_FILE_TTL_HOURS", "24"))
    )
    template_dir: str = field(
        default_factory=lambda: os.environ.get("TEMPLATE_DIR", str(_BACKEND_DIR / "templete"))
    )
    generated_dir: str = field(
        default_factory=lambda: os.environ.get("GENERATED_DIR", str(_BACKEND_DIR / "generated"))
    )
    gemini_resume_model: str = field(
        default_factory=lambda: os.environ.get("GEMINI_RESUME_MODEL", "gemini-2.5-flash")
    )
    allowed_origins: list[str] = field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.environ.get(
                "ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000"
            ).split(",")
            if origin.strip()
        ]
    )

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
