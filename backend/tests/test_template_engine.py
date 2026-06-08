import pytest

from app.services.template_engine import TEMPLATE_DIR, list_templates, load_metadata, render_resume

SAMPLE_RESUME = {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "phone": "+91 98765 43210",
    "location": "Mumbai, India",
    "linkedin": "linkedin.com/in/janedoe",
    "github": "github.com/janedoe",
    "portfolio": "",
    "summary": "Experienced software engineer with 5 years in full-stack development.",
    "skills": [
        {"category": "Languages", "skill_items": ["Python", "TypeScript", "Go"]},
        {"category": "Frameworks", "skill_items": ["FastAPI", "React", "Docker"]},
    ],
    "experience": [
        {
            "role": "Software Engineer",
            "company": "Acme Corp",
            "location": "Bengaluru, India",
            "start_date": "Jan 2022",
            "end_date": "Present",
            "description": [
                "Built microservices handling 10M+ daily requests using FastAPI.",
                "Reduced API latency by 40% through query optimization.",
            ],
        }
    ],
    "education": [
        {
            "degree": "B.Tech in Computer Science",
            "institution": "IIT Bombay",
            "graduation_date": "May 2021",
            "gpa": "9.1 / 10",
        }
    ],
    "projects": [
        {
            "name": "ResumeIQ",
            "technologies": "FastAPI, React, PostgreSQL, docxtpl",
            "description": ["AI-powered resume analyzer and rewriter."],
        }
    ],
    "certifications": ["AWS Certified Developer – Associate"],
    "achievements": ["1st place, National Hackathon 2022"],
}


def test_list_templates():
    templates = list_templates()
    assert isinstance(templates, list)
    assert len(templates) >= 1
    assert all("id" in template and "name" in template for template in templates)


def test_render_minimalist():
    result = render_resume(SAMPLE_RESUME, "minimalist")
    assert isinstance(result, bytes)
    assert result[:4] == b"PK\x03\x04", "Not a valid .docx (ZIP) file"


def test_render_modern_blue():
    result = render_resume(SAMPLE_RESUME, "modern_blue")
    assert isinstance(result, bytes)
    assert result[:4] == b"PK\x03\x04"


def test_missing_template_raises():
    with pytest.raises(FileNotFoundError):
        render_resume(SAMPLE_RESUME, "does_not_exist")


def test_missing_required_fields_raises():
    bad_data = {"name": "Jane", "summary": "Engineer", "experience": []}
    with pytest.raises(ValueError):
        render_resume(bad_data, "minimalist")


def test_fresher_resume_without_experience_renders():
    fresher = {
        "name": "Jane Doe",
        "summary": "",
        "experience": [],
        "education": [
            {
                "degree": "B.Tech",
                "institution": "Example University",
                "graduation_date": "2025",
            }
        ],
    }
    result = render_resume(fresher, "minimalist")
    assert result[:4] == b"PK\x03\x04"


def test_contact_line_assembled_from_parts():
    data = dict(SAMPLE_RESUME)
    data.pop("contact_line", None)
    result = render_resume(data, "minimalist")
    assert isinstance(result, bytes)


def test_template_switching_does_not_alter_source():
    """Rendering different templates must not corrupt the source .docx files."""
    meta = load_metadata()
    for template_id in meta:
        template_file = meta[template_id].get("file") or meta[template_id].get("file_name")
        path = TEMPLATE_DIR / template_file
        before = path.read_bytes()
        render_resume(SAMPLE_RESUME, template_id)
        after = path.read_bytes()
        assert before == after, f"Template file {path.name} was mutated during rendering!"
