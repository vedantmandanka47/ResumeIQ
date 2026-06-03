"""
template_engine.py — ResumeIQ DOCX rendering service
"""
import json
import tempfile
from pathlib import Path
from typing import Any

from docxtpl import DocxTemplate

from app.schemas.resume_data import ResumeOutputSchema
from app.services.templates.mapping import build_template_context

TEMPLATE_DIR = Path(__file__).parent.parent.parent / "templete"
METADATA_FILE = TEMPLATE_DIR / "template_metadata.json"


def load_metadata() -> dict:
    """Load template_metadata.json. Raises FileNotFoundError if missing."""
    if not METADATA_FILE.exists():
        raise FileNotFoundError(f"template_metadata.json not found at {METADATA_FILE}")
    return json.loads(METADATA_FILE.read_text(encoding="utf-8"))


def list_templates() -> list[dict]:
    """Return available templates sorted by 'order'."""
    meta = load_metadata()
    return sorted(
        [
            {
                "id": key,
                "name": value["name"],
                "description": value.get("description", ""),
                "preview": value.get("preview"),
            }
            for key, value in meta.items()
        ],
        key=lambda template: meta[template["id"]].get("order", 99),
    )


def _coerce_resume_dict(resume_data: dict) -> dict:
    """Normalize API payloads into ResumeOutputSchema field names."""
    coerced = dict(resume_data)
    education = coerced.get("education") or []
    fixed_education: list[dict[str, Any]] = []
    for entry in education:
        if not isinstance(entry, dict):
            continue
        row = dict(entry)
        if not row.get("school") and row.get("institution"):
            row["school"] = row["institution"]
        fixed_education.append(row)
    coerced["education"] = fixed_education

    skills = coerced.get("skills") or []
    fixed_skills: list[dict[str, Any]] = []
    for group in skills:
        if not isinstance(group, dict):
            continue
        row = dict(group)
        if "items" not in row and "skill_items" in row:
            row["items"] = row["skill_items"]
        fixed_skills.append(row)
    coerced["skills"] = fixed_skills
    return coerced


def _validate_context(context: dict) -> None:
    """Raise ValueError with a descriptive message if required fields are missing."""
    if not str(context.get("name", "")).strip():
        raise ValueError("Resume data is missing required fields: ['name']")
    if not context.get("education"):
        raise ValueError("Resume data is missing required fields: ['education']")


def render_resume(resume_data: dict, template_id: str) -> bytes:
    """
    Render a DOCX resume from structured data and a template ID.

    Args:
        resume_data: Canonical resume JSON dict (see CANONICAL_SCHEMA).
        template_id: e.g. "minimalist" or "modern_blue"

    Returns:
        Raw bytes of the rendered .docx file.

    Raises:
        FileNotFoundError: Template file not found.
        ValueError: Invalid resume data.
        RuntimeError: Rendering failure.
    """
    meta = load_metadata()
    if template_id not in meta:
        available = list(meta.keys())
        raise FileNotFoundError(f"Template '{template_id}' not found. Available: {available}")

    template_file = meta[template_id].get("file") or meta[template_id].get("file_name")
    if not template_file:
        raise FileNotFoundError(f"Template '{template_id}' has no file configured in metadata")

    template_path = TEMPLATE_DIR / template_file
    if not template_path.exists():
        raise FileNotFoundError(f"Template file missing: {template_path}")

    resume = ResumeOutputSchema.model_validate(_coerce_resume_dict(resume_data))
    context = build_template_context(resume)
    _validate_context(context)

    tpl = DocxTemplate(str(template_path))
    try:
        tpl.render(context)
    except Exception as exc:
        raise RuntimeError(f"Rendering failed: {exc}") from exc

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        tpl.save(str(tmp_path))
        return tmp_path.read_bytes()
    finally:
        tmp_path.unlink(missing_ok=True)
