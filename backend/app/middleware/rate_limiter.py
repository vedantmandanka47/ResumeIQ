"""Per-IP request rate limiting."""

from fastapi import Request
from slowapi import Limiter


def get_real_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",", maxsplit=1)[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


limiter = Limiter(key_func=get_real_ip, default_limits=[])
