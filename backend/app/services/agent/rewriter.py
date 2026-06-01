"""Two-pass resume rewrite pipeline."""

import logging
from datetime import datetime, timezone
from typing import Any

from .authenticity import format_blacklist_for_prompt
from .gemini import call_gemini
from .prompts.rewrite import REWRITE_PASS1_PROMPT, REWRITE_PASS2_PROMPT

logger = logging.getLogger(__name__)


def _build_role_instruction(target_role: str | None) -> str:
    if isinstance(target_role, str) and target_role.strip():
        return f"TARGET ROLE: Align truthful language and keywords for {target_role.strip()}."
    return "TARGET ROLE: Not specified. Optimize for general software-industry roles."


def _build_company_instruction(company_name: str | None) -> str:
    if isinstance(company_name, str) and company_name.strip():
        return f"TARGET COMPANY: Use relevant truthful language signals for {company_name.strip()}."
    return "TARGET COMPANY: Not specified."


def _derive_changes(pass1: dict[str, Any], pass2: dict[str, Any]) -> list[dict[str, str]]:
    specific_changes = pass2.get("specific_changes", [])
    if isinstance(specific_changes, list):
        normalized = []
        for change in specific_changes:
            if not isinstance(change, dict):
                continue
            before = str(change.get("before", "")).strip()
            after = str(change.get("after", "")).strip()
            reason = str(change.get("reason", "")).strip()
            section = str(change.get("section", "resume")).strip() or "resume"
            change_type = str(change.get("change_type", "improved")).strip() or "improved"
            if before or after or reason:
                normalized.append(
                    {
                        "section": section,
                        "change_type": change_type,
                        "before": before,
                        "after": after,
                        "reason": reason,
                        "description": reason
                        or f"Updated {section} from {before!r} to {after!r}.",
                    }
                )
        if normalized:
            return normalized

    changes: list[dict[str, str]] = []
    for section in pass1.get("sections_rewritten", []):
        changes.append(
            {
                "section": str(section),
                "change_type": "improved",
                "description": f"Restructured and improved the {section} section in Pass 1.",
            }
        )
    for flag in pass2.get("authenticity_flags", []):
        if isinstance(flag, dict):
            changes.append(
                {
                    "section": "language",
                    "change_type": "removed",
                    "description": (
                        f"Replaced generic phrase {flag.get('phrase', '')!r} with "
                        f"{flag.get('replacement', '')!r}."
                    ),
                }
            )
    for _fix in pass2.get("vague_bullets_fixed", []):
        changes.append(
            {
                "section": "bullets",
                "change_type": "restructured",
                "before": str(_fix.get("original_bullet", "")) if isinstance(_fix, dict) else "",
                "after": str(_fix.get("fixed_bullet", "")) if isinstance(_fix, dict) else "",
                "reason": "Made a vague bullet more specific using source details.",
                "description": "Made a vague bullet more specific using source details.",
            }
        )
    return changes


def _frontend_change_log(changes: list[dict[str, str]]) -> list[dict[str, str]]:
    type_map = {"improved": "modification", "removed": "deletion", "restructured": "modification"}
    return [
        {
            "type": type_map.get(change.get("change_type", ""), "modification"),
            "description": change.get("description", ""),
            "section": change.get("section", ""),
            "before": change.get("before", ""),
            "after": change.get("after", ""),
            "reason": change.get("reason", change.get("description", "")),
        }
        for change in changes
    ]


def _rewrite_payload(
    raw_text: str,
    rewritten_text: str,
    pass1_completed_at: str,
    pass2_completed_at: str,
    changes: list[dict[str, str]],
    authenticity: dict[str, Any],
    status: str,
) -> dict[str, Any]:
    """Add canonical and current-frontend aliases to a rewrite response."""
    return {
        "original_text": raw_text,
        "rewritten_text": rewritten_text,
        "original_text_preview": raw_text,
        "rewritten_text_preview": rewritten_text,
        "changes": changes,
        "changes_json": changes,
        "change_log": _frontend_change_log(changes),
        "authenticity": authenticity,
        "authenticity_json": authenticity,
        "authenticity_flags": authenticity.get("authenticity_flags", []),
        "vague_bullets_fixed": authenticity.get("vague_bullets_fixed", []),
        "personal_details_preserved": authenticity.get("personal_details_preserved", True),
        "authenticity_check_status": status,
        "pass1_completed_at": pass1_completed_at,
        "pass2_completed_at": pass2_completed_at,
    }


async def rewrite(
    raw_text: str,
    analysis: dict[str, Any],
    target_role: str | None = None,
    company_name: str | None = None,
) -> dict[str, Any]:
    """Rewrite a resume structurally, then remove generic AI-style language."""
    if not isinstance(raw_text, str) or not raw_text.strip():
        return {"error": "REWRITE_PASS1_FAILED", "reason": "Resume text is empty"}
    if not isinstance(analysis, dict) or "error" in analysis:
        return {"error": "REWRITE_PASS1_FAILED", "reason": "A valid analysis is required"}

    pass1 = await call_gemini(
        REWRITE_PASS1_PROMPT.format(
            resume_text=raw_text,
            target_role_instruction=_build_role_instruction(target_role),
            company_instruction=_build_company_instruction(company_name),
        ),
        expect_json=True,
    )
    pass1_completed_at = datetime.now(timezone.utc).isoformat()
    if not isinstance(pass1, dict) or "error" in pass1:
        return pass1

    rewritten_text = pass1.get("rewritten_text")
    if not isinstance(rewritten_text, str) or not rewritten_text.strip():
        return {"error": "REWRITE_PASS1_FAILED", "reason": "Pass 1 returned empty rewritten text"}

    pass2 = await call_gemini(
        REWRITE_PASS2_PROMPT.format(
            blacklist_formatted=format_blacklist_for_prompt(),
            rewritten_text=rewritten_text,
            original_text=raw_text,
        ),
        expect_json=True,
    )
    pass2_completed_at = datetime.now(timezone.utc).isoformat()
    if not isinstance(pass2, dict) or "error" in pass2:
        logger.warning("Rewrite Pass 2 failed; returning Pass 1 output")
        return _rewrite_payload(
            raw_text,
            rewritten_text,
            pass1_completed_at,
            pass2_completed_at,
            [{"section": "all", "change_type": "improved", "description": "Pass 1 rewrite applied."}],
            {"authenticity_flags": [], "vague_bullets_fixed": []},
            "FAILED",
        )

    changes = _derive_changes(pass1, pass2)
    if pass2.get("personal_details_preserved") is not True:
        logger.warning("Authenticity pass reported dropped personal details; returning Pass 1 output")
        return _rewrite_payload(
            raw_text,
            rewritten_text,
            pass1_completed_at,
            pass2_completed_at,
            changes,
            pass2,
            "FAILED",
        )

    final_text = pass2.get("final_text", rewritten_text)
    if not isinstance(final_text, str) or not final_text.strip():
        final_text = rewritten_text
    return _rewrite_payload(
        raw_text,
        final_text,
        pass1_completed_at,
        pass2_completed_at,
        changes,
        pass2,
        "PASSED",
    )

