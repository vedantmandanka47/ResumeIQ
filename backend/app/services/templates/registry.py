"""Dynamic DOCX template registry."""

import json
from dataclasses import dataclass
from pathlib import Path

from app.config import settings


@dataclass(frozen=True)
class TemplateMetadata:
    id: str
    name: str
    description: str
    file_name: str
    primary_color: str
    path: Path


class TemplateNotFoundError(ValueError):
    """Raised when a requested template id is unknown."""


def _metadata_path() -> Path:
    return Path(settings.template_dir) / "template_metadata.json"


def _iter_metadata_entries(raw: object) -> list[dict[str, object]]:
    if isinstance(raw, dict):
        return [
            {
                "id": str(value.get("id", key)),
                "name": str(value.get("name", key)),
                "description": str(value.get("description", "")),
                "file_name": str(value.get("file") or value.get("file_name", "")),
                "primary_color": str(value.get("primary_color", "#475569")),
                "order": int(value.get("order", 99)),
            }
            for key, value in raw.items()
            if isinstance(value, dict)
        ]
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    return []


def list_templates() -> list[TemplateMetadata]:
    template_dir = Path(settings.template_dir)
    with _metadata_path().open("r", encoding="utf-8") as handle:
        raw_items = _iter_metadata_entries(json.load(handle))

    templates: list[TemplateMetadata] = []
    for item in sorted(raw_items, key=lambda entry: int(entry.get("order", 99))):
        file_name = str(item.get("file_name") or item.get("file") or "")
        if not file_name:
            continue
        path = (template_dir / file_name).resolve()
        if path.suffix.lower() != ".docx" or not path.exists():
            continue
        templates.append(
            TemplateMetadata(
                id=str(item["id"]),
                name=str(item["name"]),
                description=str(item.get("description", "")),
                file_name=file_name,
                primary_color=str(item.get("primary_color", "#475569")),
                path=path,
            )
        )
    return templates


def get_template(template_id: str | None = None) -> TemplateMetadata:
    templates = list_templates()
    if not templates:
        raise TemplateNotFoundError("No DOCX templates are available")
    if not template_id:
        return templates[0]
    for template in templates:
        if template.id == template_id:
            return template
    raise TemplateNotFoundError(f"Template {template_id!r} was not found")
