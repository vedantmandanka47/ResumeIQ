"""Render canonical resume data into DOCX templates."""

from pathlib import Path

from docxtpl import DocxTemplate

from app.schemas.resume_data import ResumeOutputSchema
from app.services.templates.mapping import build_template_context
from app.services.templates.registry import TemplateMetadata
from app.services.templates.validator import validate_template


def render_resume_docx(
    *,
    resume: ResumeOutputSchema,
    template: TemplateMetadata,
    output_path: Path,
) -> Path:
    validate_template(template.path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    document = DocxTemplate(str(template.path))
    document.render(build_template_context(resume))
    document.save(str(output_path))
    return output_path
