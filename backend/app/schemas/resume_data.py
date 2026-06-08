from pydantic import BaseModel, Field


class ExperienceEntry(BaseModel):
    role: str = Field(default="", description="The job title or role held by the candidate")
    company: str = Field(default="", description="Name of the company or organization")
    location: str = Field(
        default="",
        description="Physical location of the company (e.g. City, State or City, Country or Remote)"
    )
    start_date: str = Field(default="", description="Start date of the employment")
    end_date: str = Field(default="", description="End date of the employment")
    description: list[str] = Field(
        default_factory=list,
        description="Bullet points describing key achievements, responsibilities, and impact. Avoid generic text."
    )


class ProjectEntry(BaseModel):
    name: str = Field(default="", description="Name of the project")
    technologies: str = Field(
        default="",
        description="Comma-separated list of key technologies used (e.g. 'Python, FastAPI, React')"
    )
    description: list[str] = Field(
        default_factory=list,
        description="Bullet points describing the project goals, implementation details, and outcomes"
    )


class EducationEntry(BaseModel):
    degree: str = Field(
        default="",
        description="The degree or certification obtained (e.g. Bachelor of Science in Computer Science)"
    )
    school: str = Field(default="", description="Name of the educational institution")
    location: str = Field(default="", description="Location of the school (e.g. City, State)")
    graduation_date: str = Field(
        default="",
        description="Graduation date or expected graduation date (e.g. Month Year or Year)"
    )
    gpa: str = Field(default="", description="GPA if available")


class SkillCategory(BaseModel):
    category: str = Field(
        default="",
        description="Category of the skills (e.g. 'Languages', 'Frameworks', 'Tools', 'Databases')"
    )
    items: list[str] = Field(default_factory=list, description="List of specific skills under this category")


class ResumeOutputSchema(BaseModel):
    """Canonical unified resume schema used by Gemini, cache, templates, and API."""

    name: str = Field(default="", description="Full name of the candidate")
    email: str = Field(default="", description="Professional email address")
    phone: str = Field(default="", description="Contact phone number")
    location: str = Field(default="", description="Current location (e.g. City, State)")
    linkedin: str = Field(default="", description="LinkedIn profile URL or handle")
    github: str = Field(default="", description="GitHub profile URL or handle")
    portfolio: str = Field(default="", description="Personal website or portfolio URL")
    summary: str = Field(default="", description="Professional summary")
    skills: list[SkillCategory] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
