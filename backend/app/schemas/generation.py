"""Request/response schemas for resume generation."""

from uuid import UUID

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    session_id: UUID
    template_id: str | None = None
    job_description: str | None = Field(default=None, max_length=12000)
    rewrite_instructions: str | None = Field(default=None, max_length=4000)


class ChangeTemplateRequest(BaseModel):
    generation_id: UUID
    template_id: str


class TemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    primary_color: str


class GenerateResponse(BaseModel):
    id: UUID
    session_id: UUID
    template_id: str
    resume_hash: str
    cache_hit: bool
    structured_cache_hit: bool
    template_switch: bool = False
    docx_available: bool
    pdf_available: bool
    pdf_error: str | None = None
    files_expired: bool = False
    download_docx_url: str | None = None
    download_pdf_url: str | None = None
    preview_url: str | None = None
    templates: list[TemplateResponse]
