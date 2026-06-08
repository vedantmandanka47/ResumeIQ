"""End-to-end resume generation orchestration."""

import logging
import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GeneratedResume, ResumeSession, RewriteResult, StructuredResume
from app.schemas.resume_data import ResumeOutputSchema
from app.services.file_manager import expiration_time, generated_docx_dir, generated_pdf_dir, get_generated_dir
from app.services.gemini.structured_output import generate_structured_resume
from app.services.pdf_converter import convert_docx_to_pdf
from app.services.resume_hash import hash_resume_content
from app.services.templates.registry import TemplateMetadata, get_template, list_templates
from app.services.templates.renderer import render_resume_docx

logger = logging.getLogger(__name__)


def _to_relative(absolute_path: Path) -> str:
    """Store only the path component relative to GENERATED_DIR."""
    return str(absolute_path.relative_to(get_generated_dir()))


def _from_relative(relative_path: str) -> Path:
    """Resolve a stored relative path back to an absolute path."""
    return get_generated_dir() / relative_path


@dataclass(frozen=True)
class GenerationResult:
    record: GeneratedResume
    structured_resume: StructuredResume
    structured_cache_hit: bool
    template_switch: bool = False


async def _latest_rewrite_text(db: AsyncSession, session_id: uuid.UUID) -> str | None:
    statement = (
        select(RewriteResult.rewritten_text)
        .where(RewriteResult.session_id == session_id)
        .order_by(RewriteResult.created_at.desc())
        .limit(1)
    )
    rewritten = (await db.execute(statement)).scalar_one_or_none()
    if isinstance(rewritten, str) and rewritten.strip():
        return rewritten
    return None


async def _resume_source_text(db: AsyncSession, session: ResumeSession) -> str:
    rewritten = await _latest_rewrite_text(db, session.id)
    if rewritten:
        return rewritten
    return session.raw_text


def public_templates() -> list[dict[str, str]]:
    return [
        {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "primary_color": template.primary_color,
        }
        for template in list_templates()
    ]


async def get_or_create_structured_resume(
    *,
    db: AsyncSession,
    session: ResumeSession,
    template_id: str,
    job_description: str | None,
    rewrite_instructions: str | None,
) -> tuple[StructuredResume, bool]:
    source_text = await _resume_source_text(db, session)
    resume_hash = hash_resume_content(
        source_text,
        job_description=job_description,
        rewrite_instructions=rewrite_instructions,
    )
    existing = (
        await db.execute(select(StructuredResume).where(StructuredResume.resume_hash == resume_hash))
    ).scalar_one_or_none()
    if existing is not None:
        existing.active_template = template_id
        await db.commit()
        await db.refresh(existing)
        return existing, True

    structured = await generate_structured_resume(
        resume_text=source_text,
        job_description=job_description,
        rewrite_instructions=rewrite_instructions,
        session_id=str(session.id),
    )
    record = StructuredResume(
        resume_hash=resume_hash,
        structured_resume_json=structured.model_dump(),
        active_template=template_id,
    )
    db.add(record)
    try:
        await db.commit()
        await db.refresh(record)
        return record, False
    except IntegrityError:
        logger.info("Structured resume hash race detected for hash=%s; reusing existing cache", resume_hash)
        await db.rollback()
        existing = (
            await db.execute(select(StructuredResume).where(StructuredResume.resume_hash == resume_hash))
        ).scalar_one()
        existing.active_template = template_id
        await db.commit()
        await db.refresh(existing)
        return existing, True


def render_generated_files(
    *,
    structured_resume: StructuredResume,
    template: TemplateMetadata,
    generation_id: uuid.UUID,
) -> tuple[Path, Path | None, str | None]:
    resume = ResumeOutputSchema.model_validate(structured_resume.structured_resume_json)
    docx_path = generated_docx_dir() / f"{generation_id}.docx"
    pdf_path = generated_pdf_dir() / f"{generation_id}.pdf"
    render_resume_docx(resume=resume, template=template, output_path=docx_path)
    converted_pdf_path, pdf_error = convert_docx_to_pdf(docx_path, pdf_path)
    return docx_path, converted_pdf_path, pdf_error


async def create_generation(
    *,
    db: AsyncSession,
    session: ResumeSession,
    template_id: str | None,
    job_description: str | None,
    rewrite_instructions: str | None,
) -> GenerationResult:
    template = get_template(template_id)
    structured_resume, cache_hit = await get_or_create_structured_resume(
        db=db,
        session=session,
        template_id=template.id,
        job_description=job_description,
        rewrite_instructions=rewrite_instructions,
    )

    generation_id = uuid.uuid4()
    docx_path, pdf_path, pdf_error = render_generated_files(
        structured_resume=structured_resume,
        template=template,
        generation_id=generation_id,
    )

    record = GeneratedResume(
        id=generation_id,
        session_id=session.id,
        structured_resume_id=structured_resume.id,
        template_id=template.id,
        docx_path=_to_relative(docx_path),
        pdf_path=_to_relative(pdf_path) if pdf_path else None,
        pdf_error=pdf_error,
        expires_at=expiration_time(),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return GenerationResult(
        record=record,
        structured_resume=structured_resume,
        structured_cache_hit=cache_hit,
        template_switch=False,
    )


async def switch_template(
    *,
    db: AsyncSession,
    generation: GeneratedResume,
    template_id: str,
) -> GenerationResult:
    template = get_template(template_id)
    generation_id = uuid.uuid4()
    docx_path, pdf_path, pdf_error = render_generated_files(
        structured_resume=generation.structured_resume,
        template=template,
        generation_id=generation_id,
    )
    generation.structured_resume.active_template = template.id
    record = GeneratedResume(
        id=generation_id,
        session_id=generation.session_id,
        structured_resume_id=generation.structured_resume_id,
        template_id=template.id,
        docx_path=_to_relative(docx_path),
        pdf_path=_to_relative(pdf_path) if pdf_path else None,
        pdf_error=pdf_error,
        expires_at=expiration_time(),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return GenerationResult(
        record=record,
        structured_resume=generation.structured_resume,
        structured_cache_hit=True,
        template_switch=True,
    )
