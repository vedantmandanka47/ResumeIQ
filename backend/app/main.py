"""ResumeIQ FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.config import settings, validate_env
from app.database import dispose_db, get_session_factory, init_db
from app.logging_config import setup_logging
from app.middleware.rate_limiter import limiter
from app.routers import generation, health, resume
from app.services.file_manager import cleanup_expired_files, cleanup_orphan_files, ensure_generated_dirs
from app.services.templates.registry import list_templates

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_env()
    await init_db()
    ensure_generated_dirs()
    if not list_templates():
        logger.warning(
            "No DOCX templates found in %s. Run: python create_canonical_docx_templates.py",
            settings.template_dir,
        )
    try:
        async with get_session_factory()() as session:
            removed_records = await cleanup_expired_files(session)
            active_paths = set()
            from sqlalchemy import select
            from app.models import GeneratedResume

            records = (await session.execute(select(GeneratedResume))).scalars().all()
            for record in records:
                active_paths.add(record.docx_path)
                if record.pdf_path:
                    active_paths.add(record.pdf_path)
            removed_files = cleanup_orphan_files(active_paths)
            if removed_records or removed_files:
                logger.info(
                    "Generated file cleanup removed records=%s files=%s",
                    removed_records,
                    removed_files,
                )
    except Exception as exc:
        logger.warning("Generated file startup cleanup failed: %s", exc, exc_info=True)
    logger.info("ResumeIQ v%s started successfully", settings.app_version)
    yield
    await dispose_db()
    logger.info("ResumeIQ shut down successfully")


def create_app() -> FastAPI:
    application = FastAPI(
        title="ResumeIQ API",
        version=settings.app_version,
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.state.limiter = limiter
    application.include_router(health.router)
    application.include_router(resume.router)
    application.include_router(generation.router)

    @application.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded. Please try again later.", "code": "RATE_LIMITED"},
        )

    @application.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, list):
            detail = "; ".join(str(item) for item in detail)
        message = str(detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": message, "code": str(exc.status_code), "detail": message},
        )

    @application.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "Unhandled exception on %s %s: %s",
            request.method,
            request.url,
            exc,
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={"error": "Something went wrong", "code": "INTERNAL"},
        )

    return application


app = create_app()
