"""Map canonical resume JSON to a docxtpl rendering context."""

from typing import Any

from app.schemas.resume_data import ResumeOutputSchema


def _join_contact(*values: str) -> str:
    return " | ".join(value for value in values if value)


def _docx_text(value: str) -> str:
    """Avoid DOCX/XML issues with bare ampersands in rendered output."""
    cleaned = value.replace("&", " and ")
    return " ".join(cleaned.split())


def _fallback_summary(resume: ResumeOutputSchema) -> str:
    if resume.summary.strip():
        return resume.summary.strip()

    if resume.education:
        edu = resume.education[0]
        degree = _docx_text(edu.degree)
        school = _docx_text(edu.school)
        grad = edu.graduation_date.strip()
        if degree and school and grad:
            return (
                f"Recent graduate pursuing opportunities in {degree}, "
                f"completing studies at {school} (expected {grad})."
            )
        if degree and school:
            return f"Candidate with academic training in {degree} from {school}."
        if degree:
            return f"Candidate with academic background in {degree}."

    if resume.projects:
        project = resume.projects[0]
        name = project.name.strip()
        if name:
            return f"Motivated candidate with hands-on project experience including {name}."

    return "Motivated candidate eager to contribute strong academic foundations and practical skills."


def _normalize_skills(resume: ResumeOutputSchema) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for group in resume.skills:
        items = [item.strip() for item in group.items if item and item.strip()]
        category = group.category.strip()
        if category and items:
            groups.append({"category": category, "skill_items": items})
    return groups


def _normalize_education(resume: ResumeOutputSchema) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for entry in resume.education:
        degree = entry.degree.strip()
        school = entry.school.strip()
        if not degree and not school:
            continue
        entries.append(
            {
                "degree": _docx_text(degree),
                "institution": _docx_text(school),
                "graduation_date": entry.graduation_date.strip(),
                "gpa": entry.gpa.strip() or None,
                "location": entry.location.strip(),
            }
        )
    return entries


def _normalize_experience(resume: ResumeOutputSchema) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for entry in resume.experience:
        bullets = [line.strip() for line in entry.description if line and line.strip()]
        role = entry.role.strip()
        company = entry.company.strip()
        if not role and not company and not bullets:
            continue
        entries.append(
            {
                "role": role,
                "company": company,
                "location": entry.location.strip(),
                "start_date": entry.start_date.strip(),
                "end_date": entry.end_date.strip(),
                "description": bullets,
            }
        )
    return entries


def _normalize_projects(resume: ResumeOutputSchema) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for entry in resume.projects:
        bullets = [line.strip() for line in entry.description if line and line.strip()]
        name = entry.name.strip()
        if not name and not bullets:
            continue
        entries.append(
            {
                "name": name,
                "technologies": entry.technologies.strip(),
                "description": bullets,
            }
        )
    return entries


def build_template_context(resume: ResumeOutputSchema) -> dict[str, Any]:
    summary = _fallback_summary(resume)
    skills = _normalize_skills(resume)
    experience = _normalize_experience(resume)
    education = _normalize_education(resume)
    projects = _normalize_projects(resume)
    certifications = [item.strip() for item in resume.certifications if item and item.strip()]
    achievements = [item.strip() for item in resume.achievements if item and item.strip()]

    return {
        "name": _docx_text(resume.name),
        "contact_line": _join_contact(
            resume.email,
            resume.phone,
            resume.location,
            resume.linkedin,
            resume.github,
            resume.portfolio,
        ),
        "summary": summary,
        "skills": skills,
        "experience": experience,
        "education": education,
        "projects": projects,
        "certifications": certifications,
        "achievements": achievements,
        "has_summary": bool(summary),
        "has_skills": bool(skills),
        "has_experience": bool(experience),
        "has_education": bool(education),
        "has_projects": bool(projects),
        "has_certifications": bool(certifications),
        "has_achievements": bool(achievements),
    }
