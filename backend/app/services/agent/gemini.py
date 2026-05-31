"""Central Gemini client and guarded response parser."""

import json
import logging
import os
import re
from typing import Any

from google import genai  # Current unified Gemini SDK recommended by Google.
from google.genai import types

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
_clients: dict[str, Any] = {}


def _get_client(model_name: str = DEFAULT_MODEL) -> Any:
    """Return a cached Gemini model client."""
    client = _clients.get(model_name)
    if client is None:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY is not configured")
        client = genai.Client(api_key=api_key)
        _clients[model_name] = client
    return client


def _strip_markdown_fences(response_text: str) -> str:
    """Remove JSON markdown fences that models sometimes add."""
    cleaned = re.sub(r"^\s*```(?:json)?\s*", "", response_text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned)
    return cleaned.strip()


async def call_gemini(
    prompt: str,
    expect_json: bool = True,
    use_search: bool = False,
    model_name: str = DEFAULT_MODEL,
) -> dict[str, Any] | str:
    """Call Gemini and return a parsed response or an error dictionary."""
    try:
        client = _get_client(model_name)
        config = None
        if use_search:
            config = types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
        )
        response_text = response.text.strip()
        if not expect_json:
            return response_text

        cleaned = _strip_markdown_fences(response_text)
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error("Gemini JSON parsing failed: %s", exc)
            return {
                "error": "PARSE_FAILED",
                "reason": f"Model returned invalid JSON: {exc}",
                "raw_preview": response_text[:200],
            }

        if not isinstance(parsed, dict):
            return {
                "error": "PARSE_FAILED",
                "reason": "Model returned JSON that was not an object",
            }
        return parsed
    except Exception as exc:
        logger.error("Gemini call failed: %s", exc, exc_info=True)
        return {"error": "LLM_ERROR", "reason": str(exc)}
