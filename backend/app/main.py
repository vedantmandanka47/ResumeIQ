"""ResumeIQ FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.config import settings, validate_env
from app.database import dispose_db, init_db
from app.logging_config import setup_logging
from app.middleware.rate_limiter import limiter
from app.routers import health, resume

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_env()
    await init_db()
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

    @application.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded. Please try again later.", "code": "RATE_LIMITED"},
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
