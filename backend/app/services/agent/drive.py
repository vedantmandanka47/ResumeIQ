"""Google Drive REST export for rewritten resumes and roadmaps."""

import asyncio
import json
import logging
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)

DRIVE_TOKEN_URL = "https://oauth2.googleapis.com/token"
DRIVE_UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart"


def _get_access_token() -> str:
    response = requests.post(
        DRIVE_TOKEN_URL,
        data={
            "client_id": os.environ["GOOGLE_DRIVE_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_DRIVE_CLIENT_SECRET"],
            "refresh_token": os.environ["GOOGLE_DRIVE_REFRESH_TOKEN"],
            "grant_type": "refresh_token",
        },
        timeout=20,
    )
    if response.status_code != 200:
        raise RuntimeError(f"OAuth token refresh failed: {response.text}")
    access_token = response.json().get("access_token")
    if not access_token:
        raise RuntimeError("OAuth token refresh returned no access token")
    return str(access_token)


def _format_doc_content(rewritten_text: str, roadmap: dict[str, Any]) -> str:
    lines = ["REWRITTEN RESUME", "=" * 40, "", rewritten_text, "", ""]
    if roadmap:
        lines += ["IMPROVEMENT ROADMAP", "=" * 40, ""]
        if roadmap.get("overall_gap_summary"):
            lines += [str(roadmap["overall_gap_summary"]), ""]
        for item in roadmap.get("items", []):
            if not isinstance(item, dict):
                continue
            lines.append(f"{item.get('order', '?')}. {item.get('action', '')}")
            lines.append(f"   Why: {item.get('why', '')}")
            lines.append(f"   Timeline: {item.get('timeline', '')}")
            lines.append(f"   Done when: {item.get('done_when', '')}")
            lines.append("")
        if roadmap.get("resume_ready_estimate"):
            lines.append(f"Estimated time to resume ready: {roadmap['resume_ready_estimate']}")
    return "\n".join(lines)


def _create_drive_doc(rewritten_text: str, roadmap: dict[str, Any], session_id: str) -> str:
    access_token = _get_access_token()
    metadata = {
        "name": f"ResumeIQ - Rewritten Resume ({session_id[:8]})",
        "mimeType": "application/vnd.google-apps.document",
    }
    response = requests.post(
        DRIVE_UPLOAD_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        files={
            "metadata": (None, json.dumps(metadata), "application/json"),
            "file": (None, _format_doc_content(rewritten_text, roadmap), "text/plain"),
        },
        timeout=30,
    )
    if response.status_code not in {200, 201}:
        raise RuntimeError(f"Drive file creation failed: {response.text}")
    file_id = response.json().get("id")
    if not file_id:
        raise RuntimeError("Drive API returned no file ID")
    return f"https://docs.google.com/document/d/{file_id}/edit"


async def export_to_drive(
    rewritten_text: str,
    roadmap: dict[str, Any],
    session_id: str,
) -> str | dict[str, str]:
    """Create a Google Doc without blocking the event loop."""
    if not isinstance(rewritten_text, str) or not rewritten_text.strip():
        return {"error": "DRIVE_EXPORT_FAILED", "reason": "Rewritten resume text is empty"}
    try:
        url = await asyncio.to_thread(_create_drive_doc, rewritten_text, roadmap or {}, session_id)
        logger.info("Google Drive export successful | session_id=%s | url=%s", session_id, url)
        return url
    except Exception as exc:
        logger.error("Google Drive export failed: %s", exc, exc_info=True)
        return {"error": "DRIVE_EXPORT_FAILED", "reason": str(exc)}

