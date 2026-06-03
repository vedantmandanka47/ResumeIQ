"""Resume generation, template switching, preview, and download endpoints."""

import logging
from pathlib import Path
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.middleware.rate_limiter import limiter
from app.models import GeneratedResume, ResumeSession
from app.schemas.generation import ChangeTemplateRequest, GenerateRequest, GenerateResponse
from app.services.file_manager import generated_docx_dir, generated_pdf_dir, resolve_generated_path
from app.services.resume_generation import create_generation, public_templates, switch_template
from app.services.templates.registry import TemplateNotFoundError
from app.services.templates.validator import TemplateValidationError

logger = logging.getLogger(__name__)
router = APIRouter(tags=["generation"])


def _error(status_code: int, message: str, code: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": message, "code": code})


def _file_available(path_value: str | None, expected_dir: Path) -> bool:
    if not path_value:
        return False
    try:
        path = resolve_generated_path(path_value, expected_dir)
    except ValueError:
        return False
    return path.is_file()


def _response(result) -> GenerateResponse:
    record = result.record
    docx_available = _file_available(record.docx_path, generated_docx_dir())
    pdf_available = _file_available(record.pdf_path, generated_pdf_dir())
    files_expired = bool(
        (record.docx_path and not docx_available) or (record.pdf_path and not pdf_available)
    )

    return GenerateResponse(
        id=record.id,
        session_id=record.session_id,
        template_id=record.template_id,
        resume_hash=result.structured_resume.resume_hash,
        cache_hit=result.structured_cache_hit,
        structured_cache_hit=result.structured_cache_hit,
        template_switch=result.template_switch,
        docx_available=docx_available,
        pdf_available=pdf_available,
        pdf_error=record.pdf_error,
        files_expired=files_expired,
        download_docx_url=f"/download/{record.id}?format=docx" if docx_available else None,
        download_pdf_url=f"/download/{record.id}?format=pdf" if pdf_available else None,
        preview_url=f"/preview/{record.id}" if pdf_available else None,
        templates=public_templates(),
    )


async def _get_generated(db: AsyncSession, generation_id: UUID) -> GeneratedResume | None:
    return await db.get(GeneratedResume, generation_id)


@router.get("/templates", response_model=None)
async def get_templates() -> dict[str, object]:
    return {"templates": public_templates()}


@router.post("/generate", response_model=GenerateResponse)
@limiter.limit(settings.rate_limit_post)
async def generate_resume(
    request: Request,
    body: GenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> GenerateResponse | JSONResponse:
    session = await db.get(ResumeSession, body.session_id)
    if session is None:
        return _error(404, "Session not found", "SESSION_NOT_FOUND")

    try:
        result = await create_generation(
            db=db,
            session=session,
            template_id=body.template_id,
            job_description=body.job_description,
            rewrite_instructions=body.rewrite_instructions,
        )
        return _response(result)
    except TemplateNotFoundError as exc:
        return _error(404, str(exc), "TEMPLATE_NOT_FOUND")
    except TemplateValidationError as exc:
        logger.error("Template validation failed: %s", exc)
        return _error(422, str(exc), "TEMPLATE_INVALID")
    except Exception as exc:
        logger.error("Resume generation failed: %s", exc, exc_info=True)
        return _error(502, "Failed to generate resume", "GENERATION_FAILED")


@router.post("/change-template", response_model=GenerateResponse)
@limiter.limit(settings.rate_limit_post)
async def change_template(
    request: Request,
    body: ChangeTemplateRequest,
    db: AsyncSession = Depends(get_db),
) -> GenerateResponse | JSONResponse:
    generation = await _get_generated(db, body.generation_id)
    if generation is None:
        return _error(404, "Generated resume not found", "GENERATION_NOT_FOUND")

    try:
        result = await switch_template(db=db, generation=generation, template_id=body.template_id)
        return _response(result)
    except TemplateNotFoundError as exc:
        return _error(404, str(exc), "TEMPLATE_NOT_FOUND")
    except TemplateValidationError as exc:
        logger.error("Template validation failed: %s", exc)
        return _error(422, str(exc), "TEMPLATE_INVALID")
    except Exception as exc:
        logger.error("Template switch failed: %s", exc, exc_info=True)
        return _error(502, "Failed to switch template", "TEMPLATE_SWITCH_FAILED")


@router.get("/download/{generation_id}", response_model=None)
async def download_generated_resume(
    generation_id: UUID,
    format: Literal["docx", "pdf"] = Query(default="docx"),
    db: AsyncSession = Depends(get_db),
) -> FileResponse | JSONResponse:
    generation = await _get_generated(db, generation_id)
    if generation is None:
        return _error(404, "Generated resume not found", "GENERATION_NOT_FOUND")

    if format == "pdf":
        if not generation.pdf_path:
            return _error(404, "PDF is not available for this generated resume", "PDF_NOT_AVAILABLE")
        path = resolve_generated_path(generation.pdf_path, generated_pdf_dir())
        media_type = "application/pdf"
    else:
        path = resolve_generated_path(generation.docx_path, generated_docx_dir())
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    if not path.exists() or not path.is_file():
        return _error(
            410,
            "Generated file has expired or was removed. Regenerate the resume to download again.",
            "FILE_GONE",
        )

    filename = f"resume-{generation.template_id}.{format}"
    return FileResponse(path, media_type=media_type, filename=filename)


@router.get("/preview/{generation_id}", response_model=None)
async def preview_generated_resume(
    generation_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> FileResponse | JSONResponse:
    generation = await _get_generated(db, generation_id)
    if generation is None:
        return _error(404, "Generated resume not found", "GENERATION_NOT_FOUND")
    if not generation.pdf_path:
        return _error(404, "PDF preview is not available; DOCX download is still available", "PDF_NOT_AVAILABLE")

    path = resolve_generated_path(generation.pdf_path, generated_pdf_dir())
    if not path.exists() or not path.is_file():
        return _error(
            410,
            "Generated preview has expired or was removed. Regenerate the resume to preview again.",
            "FILE_GONE",
        )
    return FileResponse(
        path,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="resume-{generation.template_id}.pdf"'},
    )
