"""
ResumeIQ — Health Check Router
Implements all four Phase 0 health endpoints:
  GET /health          → app liveness
  GET /health/db       → PostgreSQL connectivity
  GET /health/llm      → Gemini connectivity
  GET /health/mcp      → MongoDB MCP connectivity
"""

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import check_db_connection
from app.llm import check_llm_connection
from app.mcp import check_mcp_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="Application liveness check")
async def health_root() -> JSONResponse:
    """
    Returns 200 if the application process is running.
    Does NOT check external dependencies — use the sub-routes for that.
    """
    settings = get_settings()
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "version": settings.app_version, "env": settings.app_env},
    )


@router.get("/db", summary="PostgreSQL connectivity check")
async def health_db() -> JSONResponse:
    """
    Attempts a SELECT 1 against PostgreSQL.
    Returns 200 + {db: connected} on success, 503 + {db: error} on failure.
    """
    result = await check_db_connection()
    status_code = 200 if result.get("db") == "connected" else 503
    return JSONResponse(status_code=status_code, content=result)


@router.get("/llm", summary="Gemini LLM connectivity check")
async def health_llm() -> JSONResponse:
    """
    Sends a minimal 'reply READY' prompt to Gemini and verifies the response.
    Returns 200 + {llm: connected} on success, 503 on failure.
    """
    result = await check_llm_connection()
    status_code = 200 if result.get("llm") == "connected" else 503
    return JSONResponse(status_code=status_code, content=result)


@router.get("/mcp", summary="MongoDB MCP server connectivity check")
async def health_mcp() -> JSONResponse:
    """
    Calls the MongoDB MCP server (or direct Motor fallback) to list collections.
    Returns 200 + {mcp: connected, collections: [...]} on success, 503 on failure.
    """
    result = await check_mcp_connection()
    status_code = 200 if result.get("mcp") == "connected" else 503
    return JSONResponse(status_code=status_code, content=result)


@router.get("/all", summary="All services status in one call")
async def health_all() -> JSONResponse:
    """
    Runs all four checks concurrently and returns a combined status.
    Used by the frontend System Status page.
    """
    import asyncio  # stdlib — fine to import locally

    db_result, llm_result, mcp_result = await asyncio.gather(
        check_db_connection(),
        check_llm_connection(),
        check_mcp_connection(),
        return_exceptions=True,
    )

    # If gather returns an Exception object, convert it to an error dict
    def _safe(r):
        if isinstance(r, Exception):
            return {"error": str(r)}
        return r

    settings = get_settings()
    payload = {
        "app": {"status": "ok", "version": settings.app_version},
        "db": _safe(db_result),
        "llm": _safe(llm_result),
        "mcp": _safe(mcp_result),
    }

    all_ok = (
        _safe(db_result).get("db") == "connected"
        and _safe(llm_result).get("llm") == "connected"
        and _safe(mcp_result).get("mcp") == "connected"
    )
    overall_code = 200 if all_ok else 207  # 207 Multi-Status — partial success
    return JSONResponse(status_code=overall_code, content=payload)
