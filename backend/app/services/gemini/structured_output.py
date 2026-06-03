"""Gemini structured output generation with schema enforcement."""

import asyncio
import json
import logging
from typing import Any

from google import genai
from google.genai import types
from pydantic import ValidationError

from app.config import settings
from app.schemas.resume_data import ResumeOutputSchema
from app.services.agent.prompts.resume_generation import GENERATE_STRUCTURED_RESUME_PROMPT

logger = logging.getLogger(__name__)


class GeminiStructuredOutputError(RuntimeError):
    """Raised when structured output generation repeatedly fails."""


def _build_prompt(resume_text: str, job_description: str | None, rewrite_instructions: str) -> str:
    return GENERATE_STRUCTURED_RESUME_PROMPT.format(
        resume_text=resume_text or "",
        job_description=job_description or "",
        rewrite_instructions=rewrite_instructions or "None.",
    )


def _validate_or_raise(payload: Any) -> ResumeOutputSchema:
    """Validate payload against canonical schema."""
    try:
        return ResumeOutputSchema.model_validate(payload)
    except ValidationError as exc:
        raise GeminiStructuredOutputError(f"ResumeOutputSchema validation failed: {exc}") from exc


def _resume_response_schema() -> Any:
    return ResumeOutputSchema


async def _call_schema_enforced_gemini(prompt: str) -> Any:
    if not settings.google_api_key:
        raise GeminiStructuredOutputError("GOOGLE_API_KEY is not configured")

    client = genai.Client(api_key=settings.google_api_key)
    response = await client.aio.models.generate_content(
        model=settings.gemini_resume_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=_resume_response_schema(),
            temperature=0.2,
        ),
    )

    parsed = getattr(response, "parsed", None)
    if parsed is not None:
        return parsed

    if not response.text:
        raise GeminiStructuredOutputError("Gemini returned an empty structured response")
    return json.loads(response.text)


async def generate_structured_resume(
    *,
    resume_text: str,
    job_description: str | None = None,
    rewrite_instructions: str | None = None,
    session_id: str | None = None,
    timeout_seconds: int = 45,
    max_retries: int = 2,
) -> ResumeOutputSchema:
    """
    Generate canonical structured resume JSON from resume_text.

    Returns:
        ResumeOutputSchema validated model.

    Notes:
    - Gemini receives only resume/job/instruction text, never template data.
    - Gemini is configured with an official JSON response schema.
    - Payload is validated with Pydantic before leaving this service.
    """
    if not isinstance(resume_text, str) or not resume_text.strip():
        raise GeminiStructuredOutputError("resume_text must be a non-empty string")

    prompt = _build_prompt(
        resume_text=resume_text,
        job_description=job_description,
        rewrite_instructions=rewrite_instructions or "None.",
    )

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            logger.info(
                "Gemini structured resume generation attempt=%s session_id=%s",
                attempt + 1,
                session_id,
            )

            result = await asyncio.wait_for(
                _call_schema_enforced_gemini(prompt),
                timeout=timeout_seconds,
            )

            if not isinstance(result, dict):
                if hasattr(result, "model_dump"):
                    result = result.model_dump()
                else:
                    raise GeminiStructuredOutputError(f"Gemini returned non-dict JSON: {type(result)}")

            return _validate_or_raise(result)

        except (asyncio.TimeoutError, GeminiStructuredOutputError, ValidationError, json.JSONDecodeError) as exc:
            last_error = exc
            logger.warning(
                "Structured output generation failed attempt=%s session_id=%s err=%s",
                attempt + 1,
                session_id,
                str(exc),
                exc_info=True,
            )
            if attempt >= max_retries:
                break
            # Small backoff
            await asyncio.sleep(0.5 * (2 ** attempt))

    raise GeminiStructuredOutputError(f"Structured resume generation failed: {last_error}")
