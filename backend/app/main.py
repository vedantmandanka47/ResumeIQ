"""
ResumeIQ — FastAPI Application Entry Point
Bootstraps the app, registers middleware, mounts routers, and
installs the global exception handler (Rule 6 — never expose tracebacks).
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import get_settings
from app.database import init_db
from app.routers import health as health_router

# ---------- Logging ---------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ---------- Rate Limiter (Rule — Phase 6 baseline setup) --------------------
limiter = Limiter(key_func=get_remote_address)

# ---------- Lifespan (startup / shutdown) -----------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once on startup and once on shutdown.
    Startup: verify settings loaded, init dev DB tables.
    Shutdown: log graceful exit.
    """
    settings = get_settings()   # will sys.exit(1) if any required var is missing
    logger.info(
        "ResumeIQ v%s starting in '%s' mode", settings.app_version, settings.app_env
    )

    if settings.app_env == "development":
        # Create tables automatically in dev — use Alembic in prod
        await init_db()
        logger.info("Development DB tables verified.")

    yield  # app is running

    logger.info("ResumeIQ shutting down.")


# ---------- App Factory -----------------------------------------------------

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="ResumeIQ API",
        description=(
            "AI-powered resume analysis agent — "
            "DevPost Hackathon: Building Agents for Real-World Challenges"
        ),
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ---- Rate limiter state ------------------------------------------------
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ---- CORS --------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- Global Exception Handler (Rule 6) ---------------------------------
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Catches any unhandled exception and returns a clean error response.
        Never exposes raw Python tracebacks to the client.
        """
        logger.exception("Unhandled exception on %s %s: %s", request.method, request.url, exc)
        return JSONResponse(
            status_code=500,
            content={"error": "Something went wrong", "code": "INTERNAL"},
        )

    # ---- Routers -----------------------------------------------------------
    app.include_router(health_router.router)
    # Future routers added here per phase:
    # app.include_router(resume_router.router)

    return app


app = create_app()
