"""Sanitize small user-supplied strings before agent calls."""

import logging
import re

logger = logging.getLogger(__name__)

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+(instructions?|prompts?)", re.I),
    re.compile(r"\byou\s+are\s+now\b", re.I),
    re.compile(r"\bpretend\s+(you\s+are|to\s+be)\b", re.I),
    re.compile(r"\bforget\s+(all\s+)?(your\s+)?instructions\b", re.I),
    re.compile(r"\bsystem\s*:\s*", re.I),
    re.compile(r"<\s*/?\s*system\s*>", re.I),
    re.compile(r"\bdisregard\b.{0,30}\binstructions\b", re.I),
]
_CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_text_input(text: str | None, max_length: int = 500) -> str:
    if not text:
        return ""

    sanitized = _CONTROL_CHAR_PATTERN.sub("", str(text)[:max_length])
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(sanitized):
            logger.warning(
                "Possible prompt injection attempt detected. Pattern: %r. Input: %r",
                pattern.pattern,
                sanitized[:100],
            )
            sanitized = pattern.sub("[REMOVED]", sanitized)
    return sanitized.strip()
