"""Resume improvement roadmap generation."""

import logging
from typing import Any

from .gemini import call_gemini
from .prompts.roadmap import ROADMAP_PROMPT

logger = logging.getLogger(__name__)


def _format_critical_fixes(fixes: list[dict[str, Any]]) -> str:
    valid_fixes = [fix for fix in fixes if isinstance(fix, dict)]
    return "\n".join(
        f"Priority {fix.get('priority', '?')}: {fix.get('issue', '')} - Fix: {fix.get('fix', '')}"
        for fix in sorted(valid_fixes, key=lambda item: item.get("priority", 99))
    ) or "No critical fixes supplied."


def _format_dimensions(dimensions: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"- {dimension.get('name', 'Unknown')}: {dimension.get('score', 'N/A')}/100"
        for dimension in dimensions
        if isinstance(dimension, dict)
    ) or "No dimension scores supplied."


def _format_company_context(company_result: dict[str, Any] | None) -> str:
    if not company_result:
        return "No company-specific context available."
    gaps = "\n".join(
        f"- [{str(gap.get('severity', 'minor')).upper()}] {gap.get('gap', '')}"
        for gap in company_result.get("gap_analysis", [])
        if isinstance(gap, dict)
    ) or "- No company-specific gaps supplied."
    return (
        f"Company: {company_result.get('company_name', 'Unknown')}\n"
        f"Verdict: {company_result.get('verdict', 'N/A')}\n"
        f"Reason: {company_result.get('verdict_reason', '')}\n"
        f"Gaps:\n{gaps}"
    )


def _level_for_score(score: Any) -> str:
    if not isinstance(score, int):
        return "Unassessed"
    if score >= 80:
        return "Strong candidate"
    if score >= 60:
        return "Developing candidate"
    return "Needs focused improvement"


def _add_frontend_aliases(result: dict[str, Any], score: Any) -> None:
    """Keep the existing RoadmapPage working while retaining the richer agent schema."""
    result["current_level"] = _level_for_score(score)
    result["target_level"] = "Application-ready candidate"
    result["roadmap"] = [
        {
            "timeframe": item.get("timeline", ""),
            "task": item.get("action", ""),
            "description": f"{item.get('why', '')} Done when: {item.get('done_when', '')}".strip(),
        }
        for item in result.get("items", [])
        if isinstance(item, dict)
    ]


async def roadmap(
    analysis: dict[str, Any],
    company_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate a grounded, ordered, time-bound resume improvement plan."""
    if not isinstance(analysis, dict) or "error" in analysis:
        return {"error": "ROADMAP_FAILED", "reason": "A valid resume analysis is required"}

    result = await call_gemini(
        ROADMAP_PROMPT.format(
            overall_score=analysis.get("overall_score", "N/A"),
            mode=analysis.get("mode", "general"),
            is_fresher=analysis.get("is_fresher", False),
            critical_fixes_formatted=_format_critical_fixes(analysis.get("critical_fixes", [])),
            dimension_scores_formatted=_format_dimensions(analysis.get("dimensions", [])),
            company_context=_format_company_context(company_result),
        ),
        expect_json=True,
    )
    if not isinstance(result, dict) or "error" in result:
        return result
    if not result.get("items"):
        logger.warning("Roadmap returned no items; inserting a focused fallback")
        result["items"] = [
            {
                "order": 1,
                "action": "Resolve the highest-priority resume fix and run a fresh analysis.",
                "why": "The generated roadmap contained no specific actions.",
                "timeline": "1 week",
                "done_when": "The top fix is complete and a new analysis result is available.",
            }
        ]
    _add_frontend_aliases(result, analysis.get("overall_score"))
    return result

