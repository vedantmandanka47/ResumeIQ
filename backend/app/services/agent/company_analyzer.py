"""Live company intelligence and resume-gap analysis."""

import logging
from typing import Any

from .gemini import call_gemini
from .prompts.company import COMPANY_PROMPT

logger = logging.getLogger(__name__)

VALID_VERDICTS = {"GO", "HOLD", "REWORK"}


def _summarize_analysis(analysis: dict[str, Any]) -> tuple[str, str, str]:
    strengths = "\n".join(f"- {item}" for item in analysis.get("top_strengths", []))
    fixes = "\n".join(
        f"- Priority {fix.get('priority', '?')}: {fix.get('issue', '')}"
        for fix in analysis.get("critical_fixes", [])
        if isinstance(fix, dict)
    )
    dimensions = "\n".join(
        f"- {dimension.get('name', 'Unknown')}: {dimension.get('score', 'N/A')}/100 - "
        f"{dimension.get('verdict', '')}"
        for dimension in analysis.get("dimensions", [])
        if isinstance(dimension, dict)
    )
    return strengths or "- None supplied", fixes or "- None supplied", dimensions or "- None supplied"


async def company_analyze(
    analysis_result: dict[str, Any],
    company_name: str,
) -> dict[str, Any]:
    """Research a company with Gemini grounding and return a validated verdict."""
    if not isinstance(analysis_result, dict) or "error" in analysis_result:
        return {"error": "COMPANY_ANALYSIS_FAILED", "reason": "A valid resume analysis is required"}
    if not isinstance(company_name, str) or not company_name.strip():
        return {"error": "COMPANY_ANALYSIS_FAILED", "reason": "Company name is required"}

    company = company_name.strip()
    strengths, fixes, dimensions = _summarize_analysis(analysis_result)
    prompt = COMPANY_PROMPT.format(
        company_name=company,
        overall_score=analysis_result.get("overall_score", "N/A"),
        mode=analysis_result.get("mode", "general"),
        top_strengths_formatted=strengths,
        critical_fixes_formatted=fixes,
        dimension_scores_formatted=dimensions,
    )
    result = await call_gemini(prompt, expect_json=True, use_search=True)
    if not isinstance(result, dict) or "error" in result:
        return result

    verdict = result.get("verdict")
    if verdict not in VALID_VERDICTS:
        logger.error("Company analysis returned invalid verdict: %r", verdict)
        return {
            "error": "INVALID_VERDICT",
            "reason": f"Model returned {verdict!r}; expected GO, HOLD, or REWORK",
        }
    if not isinstance(result.get("company_signals"), dict):
        return {"error": "COMPANY_ANALYSIS_FAILED", "reason": "Company signals were missing"}
    if not result.get("gap_analysis"):
        result["gap_analysis"] = [
            {
                "gap": "No detailed company-specific gap was identified from available signals.",
                "severity": "minor",
            }
        ]
    return result

