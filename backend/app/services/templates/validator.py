"""Placeholder validation for docxtpl templates."""

from pathlib import Path

from docxtpl import DocxTemplate

REQUIRED_TEMPLATE_VARIABLES = {
    "name",
    "contact_line",
    "summary",
    "skills",
    "experience",
    "education",
    "projects",
    "certifications",
    "achievements",
    "has_summary",
    "has_skills",
    "has_experience",
    "has_education",
    "has_projects",
    "has_certifications",
    "has_achievements",
}


class TemplateValidationError(ValueError):
    """Raised when a template cannot render the canonical resume context."""


def get_template_variables(path: Path) -> set[str]:
    template = DocxTemplate(str(path))
    return set(template.get_undeclared_template_variables())


def validate_template(path: Path) -> None:
    variables = get_template_variables(path)
    missing = REQUIRED_TEMPLATE_VARIABLES - variables
    if missing:
        raise TemplateValidationError(
            f"Template {path.name} is missing required variables: {', '.join(sorted(missing))}"
        )
