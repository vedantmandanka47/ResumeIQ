"""Resume analysis pipeline with fresher-mode switching."""

import logging
from typing import Any

from .gemini import call_gemini
from .prompts.analysis import FRESHER_ANALYSIS_PROMPT, GENERAL_ANALYSIS_PROMPT, JD_SECTION

logger = logging.getLogger(__name__)

EXPECTED_DIMENSIONS = {
    "ATS Compatibility",
    "Impact & Quantification",
    "Skill Relevance",
    "Language & Authenticity",
    "Structure & Readability",
    "Completeness",
    "Competitive Standing",
}


def _validate_analysis(result: dict[str, Any], expected_mode: str) -> dict[str, Any] | None:
    score = result.get("overall_score")
    dimensions = result.get("dimensions")
    if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100:
        return {"error": "ANALYSIS_FAILED", "reason": "Analysis returned an invalid overall score"}
    if not isinstance(dimensions, list) or len(dimensions) != len(EXPECTED_DIMENSIONS):
        return {"error": "ANALYSIS_FAILED", "reason": "Analysis did not return all 7 dimensions"}

    names: set[str] = set()
    for dimension in dimensions:
        if not isinstance(dimension, dict):
            return {"error": "ANALYSIS_FAILED", "reason": "Analysis returned an invalid dimension"}
        name = dimension.get("name")
        dimension_score = dimension.get("score")
        if not isinstance(name, str) or not name.strip():
            return {"error": "ANALYSIS_FAILED", "reason": "Analysis dimension name was missing"}
        if (
            not isinstance(dimension_score, int)
            or isinstance(dimension_score, bool)
            or not 0 <= dimension_score <= 100
        ):
            return {"error": "ANALYSIS_FAILED", "reason": f"Invalid score for {name}"}
        names.add(name)

    if names != EXPECTED_DIMENSIONS:
        return {"error": "ANALYSIS_FAILED", "reason": "Analysis returned unexpected dimensions"}
    if expected_mode == "fresher":
        result["mode"] = "fresher"
        result["is_fresher"] = True
    elif result.get("mode") != "general":
        result["mode"] = "general"
    return None


def _build_jd_section(job_description: str | None) -> str:
    """Build the JD section for analysis prompts. Returns empty string if no JD."""
    if job_description and job_description.strip():
        return JD_SECTION.format(job_description=job_description.strip())
    return ""


async def analyze(
    raw_text: str,
    target_role: str | None = None,
    job_description: str | None = None,
) -> dict[str, Any]:
    """Analyze a resume and rerun with fresher calibration when needed."""
    if not isinstance(raw_text, str) or not raw_text.strip():
        return {"error": "ANALYSIS_FAILED", "reason": "Resume text is empty"}

    target = target_role.strip() if isinstance(target_role, str) and target_role.strip() else "Not specified"
    jd_section = _build_jd_section(job_description)

    result = await call_gemini(
        GENERAL_ANALYSIS_PROMPT.format(
            resume_text=raw_text,
            target_role=target,
            job_description_section=jd_section,
        ),
        expect_json=True,
    )
    if not isinstance(result, dict) or "error" in result:
        return result

    if result.get("is_fresher") is True:
        logger.info("Fresher resume detected; rerunning analysis in fresher mode")
        result = await call_gemini(
            FRESHER_ANALYSIS_PROMPT.format(
                resume_text=raw_text,
                target_role=target,
                job_description_section=jd_section,
            ),
            expect_json=True,
        )
        if not isinstance(result, dict) or "error" in result:
            return result
        error = _validate_analysis(result, "fresher")
        return error or result

    error = _validate_analysis(result, "general")
    return error or result
