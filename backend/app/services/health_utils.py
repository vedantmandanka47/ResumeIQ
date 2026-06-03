"""Normalize dependency health check payloads for the API."""

from typing import Any

_CONNECTED_STATES = frozenset({"connected", "ready", "ok"})


def normalize_service_health(service_key: str, result: Any) -> dict[str, Any]:
    """
    Return a consistent health payload: {service_key: "connected" | "error", ...}.
    """
    if not isinstance(result, dict):
        return {service_key: "error", "detail": f"Invalid health response: {type(result).__name__}"}

    raw_status = str(result.get(service_key, "error")).strip().lower()
    if raw_status in _CONNECTED_STATES:
        normalized = dict(result)
        normalized[service_key] = "connected"
        return normalized

    detail = result.get("detail") or result.get("reason") or f"Unexpected status: {raw_status or 'missing'}"
    return {service_key: "error", "detail": str(detail)}
