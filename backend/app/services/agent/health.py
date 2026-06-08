"""External dependency health checks."""

from typing import Any

from .gemini import call_gemini
from .mcp_client import _call_mcp
from .prompts.health import LLM_HEALTH_PROMPT


async def check_llm_health() -> dict[str, str]:
    """Verify Gemini connectivity without raising."""
    result = await call_gemini(LLM_HEALTH_PROMPT, expect_json=False)
    if isinstance(result, str) and result.strip().upper() == "READY":
        return {"llm": "connected"}
    if isinstance(result, dict):
        return {"llm": "error", "detail": str(result.get("reason", result))}
    return {"llm": "error", "detail": f"Unexpected response: {str(result)[:100]}"}


async def check_mcp_health() -> dict[str, Any]:
    """Verify the MCP endpoint itself rather than its direct-MongoDB fallback."""
    result = await _call_mcp("list_collections", {}, allow_fallback=False)
    if "error" in result:
        return {"mcp": "error", "detail": str(result.get("reason", "Unknown MCP error"))}
    return {"mcp": "connected", "collections": result.get("collections", [])}

