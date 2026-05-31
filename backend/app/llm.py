"""
ResumeIQ — Gemini LLM Client
Wraps google.generativeai with:
  - Connection verification (used by /health/llm)
  - Structured prompt builder (enforces the 5-section Rule 4 law)
  - Safe call wrapper (Rule 3: every LLM call in try/except with fallback)
"""

import json
import logging
from typing import Any

# Rule 2: top-level import — never use deep submodule paths
import google.generativeai as genai
from google.generativeai import types as genai_types

from app.config import get_settings

logger = logging.getLogger(__name__)


def _configure_genai() -> None:
    """Configure the SDK once using the API key from settings."""
    settings = get_settings()
    genai.configure(api_key=settings.google_api_key)


# Configure on module import — fails fast if key is absent
_configure_genai()


def get_model() -> genai.GenerativeModel:
    """Return a GenerativeModel instance using the configured model name."""
    settings = get_settings()
    return genai.GenerativeModel(model_name=settings.gemini_model)


# ---------- Prompt Builder (Rule 4 — 5-section structure) -------------------

def build_prompt(
    system_role: str,
    task_definition: str,
    input_data: str,
    output_contract: str,
    failure_instruction: str,
) -> str:
    """
    Assembles a prompt following the mandatory 5-section structure law (Rule 4).
    Never bypass this builder for LLM calls — use it every time.
    """
    return (
        f"[SYSTEM ROLE]\n{system_role.strip()}\n\n"
        f"[TASK DEFINITION]\n{task_definition.strip()}\n\n"
        f"[INPUT DATA]\n{input_data.strip()}\n\n"
        f"[OUTPUT CONTRACT]\n{output_contract.strip()}\n\n"
        f"[FAILURE INSTRUCTION]\n{failure_instruction.strip()}"
    )


# ---------- Safe LLM Call (Rule 3) ------------------------------------------

async def call_llm(
    prompt: str,
    *,
    temperature: float = 0.3,
    max_output_tokens: int = 8192,
) -> dict[str, Any]:
    """
    Sends a prompt to Gemini and returns parsed JSON.

    Always wrapped in try/except. Never lets a malformed response crash a
    caller. Returns a structured error dict on any failure so the endpoint
    can return it cleanly to the frontend.

    Args:
        prompt:            Full assembled prompt string (use build_prompt()).
        temperature:       Sampling temperature (lower = more deterministic).
        max_output_tokens: Hard cap on response length.

    Returns:
        Parsed dict on success.
        {"error": "LLM_FAILED", "reason": "..."} on any failure.
    """
    try:
        model = get_model()
        response = await model.generate_content_async(
            prompt,
            generation_config=genai_types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                response_mime_type="application/json",  # request JSON directly
            ),
        )

        raw_text = response.text.strip()

        # Strip markdown code fences if the model wraps the JSON anyway
        if raw_text.startswith("```"):
            lines = raw_text.splitlines()
            raw_text = "\n".join(
                line for line in lines if not line.startswith("```")
            ).strip()

        try:
            return json.loads(raw_text)
        except json.JSONDecodeError as parse_err:
            logger.error("LLM JSON parse error: %s | raw: %.200s", parse_err, raw_text)
            return {
                "error": "LLM_PARSE_FAILED",
                "reason": f"Model returned non-JSON output: {str(parse_err)}",
                "raw_preview": raw_text[:300],
            }

    except Exception as exc:  # noqa: BLE001 — intentional broad catch per Rule 3
        logger.exception("LLM call failed: %s", exc)
        return {"error": "LLM_FAILED", "reason": str(exc)}


# ---------- Health Check Helper ---------------------------------------------

async def check_llm_connection() -> dict[str, Any]:
    """
    Sends a minimal test prompt and verifies the response contains 'READY'.
    Used by GET /health/llm.
    """
    try:
        prompt = build_prompt(
            system_role="You are a connectivity verification assistant.",
            task_definition="Reply with the single word READY and nothing else.",
            input_data="N/A",
            output_contract='Return exactly: {"status": "READY"}',
            failure_instruction='Return: {"status": "FAILED"}',
        )

        result = await call_llm(prompt, temperature=0.0, max_output_tokens=20)

        # Accept both raw dict and string containing READY
        if isinstance(result, dict) and "READY" in str(result).upper():
            logger.info("LLM health check: OK")
            return {"llm": "connected", "model": get_settings().gemini_model}

        logger.warning("LLM health check unexpected response: %s", result)
        return {"llm": "unexpected_response", "detail": str(result)}

    except Exception as exc:
        logger.error("LLM health check failed: %s", exc)
        return {"llm": "error", "detail": str(exc)}
