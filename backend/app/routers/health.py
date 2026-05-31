"""Service health endpoints."""

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import check_db_connection
from app.services.agent_gateway import invoke

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_root() -> dict[str, str]:
    return {"status": "ok", "version": settings.app_version}


@router.get("/db")
async def health_db() -> JSONResponse:
    result = await check_db_connection()
    return JSONResponse(status_code=200 if result.get("db") == "connected" else 503, content=result)


@router.get("/llm")
async def health_llm() -> JSONResponse:
    try:
        result = await invoke("check_llm_health")
    except Exception as exc:
        logger.error("LLM health check failed: %s", exc)
        result = {"llm": "error", "detail": str(exc)}
    return JSONResponse(status_code=503 if result.get("llm") == "error" else 200, content=result)


@router.get("/mcp")
async def health_mcp() -> JSONResponse:
    try:
        result = await invoke("check_mcp_health")
    except Exception as exc:
        logger.error("MCP health check failed: %s", exc)
        result = {"mcp": "error", "detail": str(exc)}
    return JSONResponse(status_code=503 if result.get("mcp") == "error" else 200, content=result)
