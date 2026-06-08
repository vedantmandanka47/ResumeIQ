"""Job description extraction agent using Gemini search grounding."""

import logging
from typing import Any

from .gemini import call_gemini
from .prompts.jd_extractor import JD_EXTRACT_PROMPT

logger = logging.getLogger(__name__)


async def extract_jd(job_url: str) -> dict[str, Any]:
    """Extract job description content from a URL using Gemini search grounding."""
    if not job_url or not job_url.strip():
        return {"error": "JD_EXTRACT_FAILED", "reason": "Job URL is empty"}

    prompt = JD_EXTRACT_PROMPT.format(job_url=job_url.strip())

    result = await call_gemini(prompt, expect_json=True, use_search=True)
    if not isinstance(result, dict) or "error" in result:
        return result

    if "extracted_text" not in result or not result["extracted_text"].strip():
        return {"error": "JD_EXTRACT_FAILED", "reason": "Could not extract job description from URL"}

    return result
