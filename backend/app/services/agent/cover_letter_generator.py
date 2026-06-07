"""Cover letter generation agent."""

import json
import logging
from typing import Any

from .gemini import call_gemini
from .prompts.cover_letter import COVER_LETTER_PROMPT

logger = logging.getLogger(__name__)


async def cover_letter(
    raw_text: str,
    target_role: str,
    company_name: str,
    tone: str = "professional",
    analysis: dict[str, Any] | None = None,
    company_signals: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate a tailored cover letter from resume + context."""
    if not isinstance(raw_text, str) or not raw_text.strip():
        return {"error": "COVER_LETTER_FAILED", "reason": "Resume text is empty"}

    analysis_highlights = {}
    if analysis:
        analysis_highlights = {
            k: analysis.get(k)
            for k in ("top_strengths", "overall_score")
            if analysis.get(k) is not None
        }

    prompt = COVER_LETTER_PROMPT.format(
        resume_text=raw_text,
        target_role=target_role,
        company_name=company_name,
        tone=tone,
        company_signals=json.dumps(company_signals or {}, indent=2),
        analysis_highlights=json.dumps(analysis_highlights, indent=2),
    )

    result = await call_gemini(prompt, expect_json=True)
    if not isinstance(result, dict) or "error" in result:
        return result

    # Basic validation
    if "cover_letter_text" not in result:
        return {"error": "COVER_LETTER_FAILED", "reason": "Response missing cover_letter_text"}

    return result
