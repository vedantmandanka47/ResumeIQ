"""Generated resume file lifecycle management."""

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import GeneratedResume

logger = logging.getLogger(__name__)


def get_generated_dir() -> Path:
    """Return the configured GENERATED_DIR as a resolved Path."""
    return Path(settings.generated_dir).resolve()


def generated_root() -> Path:
    return get_generated_dir()


def generated_docx_dir() -> Path:
    return generated_root() / "docx"


def generated_pdf_dir() -> Path:
    return generated_root() / "pdf"


def ensure_generated_dirs() -> None:
    generated_docx_dir().mkdir(parents=True, exist_ok=True)
    generated_pdf_dir().mkdir(parents=True, exist_ok=True)


def expiration_time() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=settings.generated_file_ttl_hours)


def resolve_generated_path(path_value: str, expected_dir: Path) -> Path:
    """Resolve a stored path (relative or absolute) to a safe absolute path."""
    candidate = Path(path_value)
    if not candidate.is_absolute():
        # Relative path stored after fix 1.3 — resolve against generated root
        candidate = generated_root() / path_value
    path = candidate.resolve()
    root = expected_dir.resolve()
    if root != path and root not in path.parents:
        raise ValueError("Generated file path is outside the allowed directory")
    return path


def remove_file_if_exists(path_value: str | None, expected_dir: Path) -> None:
    if not path_value:
        return
    try:
        path = resolve_generated_path(path_value, expected_dir)
        if path.exists():
            path.unlink()
    except Exception as exc:
        logger.warning("Failed to remove generated file %s: %s", path_value, exc)


async def cleanup_expired_files(db: AsyncSession) -> int:
    ensure_generated_dirs()
    now = datetime.now(timezone.utc)
    records = (await db.execute(select(GeneratedResume).where(GeneratedResume.expires_at <= now))).scalars().all()
    for record in records:
        remove_file_if_exists(record.docx_path, generated_docx_dir())
        remove_file_if_exists(record.pdf_path, generated_pdf_dir())
    if records:
        await db.execute(delete(GeneratedResume).where(GeneratedResume.expires_at <= now))
        await db.commit()
    return len(records)


def cleanup_orphan_files(active_paths: set[str]) -> int:
    ensure_generated_dirs()
    # Resolve all active paths to absolute for comparison
    resolved_active = set()
    for p in active_paths:
        try:
            resolved_active.add(str(resolve_generated_path(p, generated_root()).resolve()))
        except (ValueError, Exception):
            resolved_active.add(p)
    removed = 0
    for directory in (generated_docx_dir(), generated_pdf_dir()):
        for path in directory.glob("*"):
            if path.is_file() and str(path.resolve()) not in resolved_active:
                try:
                    path.unlink()
                    removed += 1
                except Exception as exc:
                    logger.warning("Failed to remove orphan file %s: %s", path, exc)
    return removed
