"""Per-IP request rate limiting."""

import os

from fastapi import Request
from slowapi import Limiter


def get_real_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",", maxsplit=1)[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _make_limiter() -> Limiter:
    redis_uri = os.environ.get("REDIS_URL", "")
    if redis_uri:
        return Limiter(key_func=get_real_ip, storage_uri=redis_uri, default_limits=[])
    # Fallback: in-memory (acceptable for single-worker dev/hackathon)
    return Limiter(key_func=get_real_ip, default_limits=[])


limiter = _make_limiter()
