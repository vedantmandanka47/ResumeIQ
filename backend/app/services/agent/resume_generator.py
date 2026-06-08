"""Agent wrapper for generating canonical structured resume JSON via Gemini."""

import logging
from typing import Any

from app.services.gemini.structured_output import generate_structured_resume

logger = logging.getLogger(__name__)


async def generate_structured_resume_agent(
    *,
    resume_text: str,
    job_description: str | None = None,
    rewrite_instructions: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """
    Wrapper exposed to the agent service package.

    Returns:
    - A dict containing the validated canonical resume JSON on success
    - Or an {"error": "...", "reason": "..."} dict on failure
    """
    try:
        model = await generate_structured_resume(
            resume_text=resume_text,
            job_description=job_description,
            rewrite_instructions=rewrite_instructions,
            session_id=session_id,
        )
        return model.model_dump()
    except Exception as exc:
        logger.error("generate_structured_resume_agent failed session_id=%s: %s", session_id, exc, exc_info=True)
        return {"error": "STRUCTURED_RESUME_FAILED", "reason": str(exc)}
