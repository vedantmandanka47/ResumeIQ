"""Resume upload, analysis, rewrite, persistence, and export endpoints."""

import asyncio
import io
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.middleware.rate_limiter import limiter
from app.middleware.sanitizer import sanitize_text_input
from app.models import (
    AnalysisResult,
    CompanyResult,
    ResumeSession,
    RewriteResult,
    RoadmapResult,
    StructuredResume,
)
from app.services.resume_generation import _resume_source_text
from app.services.resume_hash import hash_resume_content
from app.schemas.analysis import AnalysisRequest
from app.schemas.company import CompanyAnalysisRequest
from app.schemas.rewrite import RewriteRequest
from app.schemas.upload import SessionResponse, UploadResponse
from app.services.agent_gateway import invoke
from app.services.docx_builder import build_resume_docx
from app.services.parser import extract_text_from_docx, extract_text_from_pdf
from app.services.template_engine import list_templates as list_docx_templates
from app.services.template_engine import render_resume as render_resume_docx

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/resume", tags=["resume"])


class ResumeRenderRequest(BaseModel):
    resume_data: dict
    template_id: str = "minimalist"


@router.get("/templates")
async def get_templates() -> list[dict]:
    """Return available DOCX templates for the template switcher."""
    return await run_in_threadpool(list_docx_templates)


@router.post("/render", response_model=None)
async def render_resume_endpoint(req: ResumeRenderRequest):
    """Render a DOCX resume from structured JSON (no Gemini call)."""
    try:
        docx_bytes = await run_in_threadpool(render_resume_docx, req.resume_data, req.template_id)
    except FileNotFoundError as exc:
        return _error(404, str(exc), "TEMPLATE_NOT_FOUND")
    except ValueError as exc:
        return _error(422, str(exc), "RENDER_VALIDATION_FAILED")
    except Exception as exc:
        logger.error("DOCX render failed: %s", exc, exc_info=True)
        return _error(500, f"Rendering failed: {exc}", "RENDER_FAILED")

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": 'inline; filename="resume.docx"',
            "Cache-Control": "no-cache",
        },
    )


@router.post("/render/download", response_model=None)
async def download_resume_endpoint(req: ResumeRenderRequest):
    """Render a DOCX resume and return it as a download."""
    try:
        docx_bytes = await run_in_threadpool(render_resume_docx, req.resume_data, req.template_id)
    except FileNotFoundError as exc:
        return _error(404, str(exc), "TEMPLATE_NOT_FOUND")
    except ValueError as exc:
        return _error(422, str(exc), "RENDER_VALIDATION_FAILED")
    except Exception as exc:
        logger.error("DOCX render download failed: %s", exc, exc_info=True)
        return _error(500, f"Rendering failed: {exc}", "RENDER_FAILED")

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="resume.docx"'},
    )


def _error(status_code: int, message: str, code: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": message, "code": code})


def _agent_error(result: Any, code: str, fallback: str) -> JSONResponse | None:
    if not isinstance(result, dict):
        return _error(502, fallback, code)
    if "error" in result:
        return _error(502, str(result.get("reason") or fallback), code)
    return None


async def _get_session(db: AsyncSession, session_id: UUID) -> ResumeSession | None:
    return await db.get(ResumeSession, session_id)


async def _get_latest(db: AsyncSession, model: Any, session_id: UUID) -> Any | None:
    statement = (
        select(model)
        .where(model.session_id == session_id)
        .order_by(model.created_at.desc())
        .limit(1)
    )
    return (await db.execute(statement)).scalar_one_or_none()


async def _store(db: AsyncSession, record: Any) -> JSONResponse | None:
    """Persist a single record. Caller is responsible for transaction scope."""
    try:
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return None
    except SQLAlchemyError as exc:
        await db.rollback()
        logger.error("DB write failed for %s: %s", type(record).__name__, exc, exc_info=True)
        return _error(500, "Database write failed", "DB_WRITE_FAILED")


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


async def _run_and_store_analysis(
    db: AsyncSession,
    session: ResumeSession,
    target_role: str | None = None,
    job_description: str | None = None,
) -> AnalysisResult | JSONResponse:
    try:
        result = await invoke(
            "analyze",
            raw_text=session.raw_text,
            target_role=target_role,
            job_description=job_description,
        )
    except Exception as exc:
        logger.error("Analysis agent call failed: %s", exc)
        return _error(502, str(exc), "ANALYSIS_FAILED")

    if error := _agent_error(result, "ANALYSIS_FAILED", "Failed to analyze resume"):
        return error

    mode = result.get("mode")
    score = result.get("overall_score")
    if mode not in {"general", "fresher"} or not isinstance(score, int) or not 0 <= score <= 100:
        logger.error("Analysis agent returned invalid summary fields: %r", result)
        return _error(502, "Analysis agent returned an invalid response", "ANALYSIS_FAILED")

    record = AnalysisResult(
        session_id=session.id,
        mode=mode,
        overall_score=score,
        target_role=target_role,
        result_json=result,
    )
    if error := await _store(db, record):
        return error
    return record


@router.post("/upload", response_model=UploadResponse)
@limiter.limit(settings.rate_limit_post)
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> UploadResponse | JSONResponse:
    filename = Path(file.filename or "").name
    suffix = Path(filename).suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        return _error(415, "Only PDF and DOCX files are supported", "UNSUPPORTED_FILE_TYPE")

    file_bytes = await file.read()
    if len(file_bytes) > settings.max_file_size_bytes:
        return _error(
            413,
            f"File exceeds the {settings.max_file_size_mb} MB size limit",
            "FILE_TOO_LARGE",
        )
    if not file_bytes:
        return _error(400, "Uploaded file is empty", "EMPTY_FILE")

    parser = extract_text_from_pdf if suffix == ".pdf" else extract_text_from_docx
    raw_text = await run_in_threadpool(parser, file_bytes)
    if not raw_text.strip():
        return _error(
            422,
            "Could not extract readable text from this file. Try a different version or format.",
            "EXTRACTION_FAILED",
        )

    record = ResumeSession(
        filename=filename[-255:],
        file_type=suffix[1:],
        raw_text=raw_text,
        char_count=len(raw_text),
    )
    if error := await _store(db, record):
        return error

    logger.info("Stored resume session %s for %s", record.id, record.filename)
    return UploadResponse(
        session_id=record.id,
        preview=raw_text[:500],
        char_count=record.char_count,
        filename=record.filename,
    )


@router.get("/benchmark", response_model=None)
async def get_benchmark() -> dict[str, Any] | JSONResponse:
    try:
        result = await invoke("get_benchmark")
    except Exception as exc:
        logger.error("Benchmark lookup failed: %s", exc)
        return _error(502, "Failed to retrieve benchmark data", "BENCHMARK_FAILED")
    if error := _agent_error(result, "BENCHMARK_FAILED", "Failed to retrieve benchmark data"):
        return error
    return result


@router.get("/{session_id}/structured-resume", response_model=None)
async def get_structured_resume(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object] | JSONResponse:
    """Return cached canonical structured resume JSON for template preview."""
    session = await _get_session(db, session_id)
    if session is None:
        return _error(404, "Session not found", "SESSION_NOT_FOUND")

    resume_hash = hash_resume_content(await _resume_source_text(db, session))
    try:
        statement = select(StructuredResume).where(StructuredResume.resume_hash == resume_hash)
        structured = (await db.execute(statement)).scalar_one_or_none()
    except ProgrammingError as exc:
        logger.error("Structured resume lookup failed (schema): %s", exc)
        return _error(
            503,
            "Structured resume storage is not ready. Run database migrations (alembic upgrade head).",
            "STRUCTURED_RESUME_SCHEMA_MISSING",
        )
    except SQLAlchemyError as exc:
        logger.error("Structured resume lookup failed: %s", exc)
        return _error(503, "Database read failed", "DATABASE_READ_FAILED")

    if structured is None:
        return _error(404, "Structured resume not found", "STRUCTURED_RESUME_NOT_FOUND")
    return {"resume_data": structured.structured_resume_json}


@router.get("/{session_id}", response_model=SessionResponse)
async def get_resume_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse | JSONResponse:
    session = await _get_session(db, session_id)
    if session is None:
        return _error(404, "Session not found", "SESSION_NOT_FOUND")
    return SessionResponse(
        session_id=session.id,
        filename=session.filename,
        char_count=session.char_count,
        file_type=session.file_type,
        created_at=session.created_at,
    )


@router.post("/{session_id}/analyze", response_model=None)
@limiter.limit(settings.rate_limit_post)
async def analyze_resume(
    request: Request,
    session_id: UUID,
    body: AnalysisRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    session = await _get_session(db, session_id)
    if session is None:
        return _error(404, "Session not found", "SESSION_NOT_FOUND")

    target_role = sanitize_text_input(body.target_role) or None
    job_description = sanitize_text_input(body.job_description) or None
    record = await _run_and_store_analysis(db, session, target_role, job_description)
    return record if isinstance(record, JSONResponse) else record.result_json


@router.post("/{session_id}/analyze/company", response_model=None)
@limiter.limit(settings.rate_limit_post)
async def analyze_company(
    request: Request,
    session_id: UUID,
    body: CompanyAnalysisRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    session = await _get_session(db, session_id)
    if session is None:
        return _error(404, "Session not found", "SESSION_NOT_FOUND")

    company_name = sanitize_text_input(body.company_name)
    if not company_name:
        return _error(422, "Company name is required", "INVALID_COMPANY_NAME")

    analysis = await _get_latest(db, AnalysisResult, session_id)
    if analysis is None:
        analysis = await _run_and_store_analysis(db, session)
        if isinstance(analysis, JSONResponse):
            return analysis

    try:
        result = await invoke(
            "company_analyze",
            analysis_result=analysis.result_json,
            company_name=company_name,
        )
    except Exception as exc:
        logger.error("Company analysis agent call failed: %s", exc)
        return _error(502, str(exc), "COMPANY_ANALYSIS_FAILED")
    if error := _agent_error(result, "COMPANY_ANALYSIS_FAILED", "Failed to analyze company fit"):
        return error

    verdict = result.get("verdict")
    if verdict not in {"GO", "HOLD", "REWORK"}:
        return _error(502, "Company analysis returned an invalid verdict", "COMPANY_ANALYSIS_FAILED")

    record = CompanyResult(
        session_id=session_id,
        company_name=company_name,
        verdict=verdict,
        result_json=result,
    )
    if error := await _store(db, record):
        return error
    return result


@router.post("/{session_id}/rewrite", response_model=None)
@limiter.limit(settings.rate_limit_post)
async def rewrite_resume(
    request: Request,
    session_id: UUID,
    body: RewriteRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    session = await _get_session(db, session_id)
    if session is None:
        return _error(404, "Session not found", "SESSION_NOT_FOUND")

    analysis = await _get_latest(db, AnalysisResult, session_id)
    if analysis is None:
        analysis = await _run_and_store_analysis(db, session)
        if isinstance(analysis, JSONResponse):
            return analysis

    target_role = sanitize_text_input(body.target_role) or None
    company_name = sanitize_text_input(body.company_name) or None
    try:
        result = await invoke(
            "rewrite",
            raw_text=session.raw_text,
            analysis=analysis.result_json,
            target_role=target_role,
            company_name=company_name,
        )
    except Exception as exc:
        logger.error("Rewrite agent call failed: %s", exc)
        return _error(502, str(exc), "REWRITE_FAILED")
    if error := _agent_error(result, "REWRITE_FAILED", "Failed to rewrite resume"):
        return error

    rewritten_text = result.get("rewritten_text") or result.get("rewritten_text_preview")
    if not isinstance(rewritten_text, str) or not rewritten_text.strip():
        return _error(502, "Rewrite agent returned no rewritten text", "REWRITE_FAILED")
    record = RewriteResult(
        session_id=session_id,
        original_text=result.get("original_text") or session.raw_text,
        rewritten_text=rewritten_text,
        changes_json=result.get("changes_json", result.get("change_log", [])),
        authenticity_json=result.get("authenticity_json", result.get("authenticity", {})),
        pass1_completed_at=_parse_datetime(result.get("pass1_completed_at")),
        pass2_completed_at=_parse_datetime(result.get("pass2_completed_at")),
    )
    if error := await _store(db, record):
        return error
    return result


@router.get("/{session_id}/rewrite/download", response_model=None)
async def download_rewrite(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse | JSONResponse:
    rewrite = await _get_latest(db, RewriteResult, session_id)
    if rewrite is None:
        return _error(404, "Rewrite not found", "REWRITE_NOT_FOUND")
    return StreamingResponse(
        io.BytesIO(rewrite.rewritten_text.encode("utf-8")),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="rewritten_resume.txt"'},
    )


@router.get("/{session_id}/rewrite/download/docx", response_model=None)
async def download_rewrite_docx(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse | JSONResponse:
    rewrite = await _get_latest(db, RewriteResult, session_id)
    if rewrite is None:
        return _error(404, "Rewrite not found", "REWRITE_NOT_FOUND")
    docx_bytes = await run_in_threadpool(build_resume_docx, rewrite.rewritten_text)
    return StreamingResponse(
        io.BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="rewritten_resume.docx"'},
    )


@router.post("/{session_id}/roadmap", response_model=None)
@limiter.limit(settings.rate_limit_post)
async def create_roadmap(
    request: Request,
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any] | JSONResponse:
    session = await _get_session(db, session_id)
    if session is None:
        return _error(404, "Session not found", "SESSION_NOT_FOUND")

    analysis = await _get_latest(db, AnalysisResult, session_id)
    if analysis is None:
        analysis = await _run_and_store_analysis(db, session)
        if isinstance(analysis, JSONResponse):
            return analysis
    company = await _get_latest(db, CompanyResult, session_id)

    try:
        result = await invoke(
            "roadmap",
            analysis=analysis.result_json,
            company_result=company.result_json if company else None,
        )
    except Exception as exc:
        logger.error("Roadmap agent call failed: %s", exc)
        return _error(502, str(exc), "ROADMAP_FAILED")
    if error := _agent_error(result, "ROADMAP_FAILED", "Failed to generate roadmap"):
        return error

    record = RoadmapResult(session_id=session_id, result_json=result)
    if error := await _store(db, record):
        return error
    return result


@router.post("/{session_id}/save", response_model=None)
@limiter.limit(settings.rate_limit_post)
async def save_snapshot(
    request: Request,
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str] | JSONResponse:
    if await _get_session(db, session_id) is None:
        return _error(404, "Session not found", "SESSION_NOT_FOUND")

    analysis = await _get_latest(db, AnalysisResult, session_id)
    company = await _get_latest(db, CompanyResult, session_id)
    rewrite = await _get_latest(db, RewriteResult, session_id)
    roadmap = await _get_latest(db, RoadmapResult, session_id)
    try:
        mongo_id = await invoke(
            "save_to_mongo",
            session_id=str(session_id),
            analysis=analysis.result_json if analysis else None,
            company_result=company.result_json if company else None,
            rewrite_result=(
                {
                    "original_text": rewrite.original_text,
                    "rewritten_text": rewrite.rewritten_text,
                    "changes": rewrite.changes_json,
                    "authenticity": rewrite.authenticity_json,
                    "pass1_completed_at": (
                        rewrite.pass1_completed_at.isoformat()
                        if rewrite.pass1_completed_at
                        else None
                    ),
                    "pass2_completed_at": (
                        rewrite.pass2_completed_at.isoformat()
                        if rewrite.pass2_completed_at
                        else None
                    ),
                }
                if rewrite
                else None
            ),
            roadmap=roadmap.result_json if roadmap else None,
        )
    except Exception as exc:
        logger.error("MongoDB snapshot save failed: %s", exc)
        return _error(502, "Failed to save to MongoDB", "MONGO_SAVE_FAILED")
    if isinstance(mongo_id, dict) and "error" in mongo_id:
        return _error(502, "Failed to save to MongoDB", "MONGO_SAVE_FAILED")
    return {"mongo_id": str(mongo_id)}


@router.get("/{session_id}/history", response_model=None)
async def get_history(session_id: UUID) -> dict[str, Any] | JSONResponse:
    try:
        snapshots = await invoke("get_history", session_id=str(session_id))
    except Exception as exc:
        logger.error("MongoDB history lookup failed: %s", exc)
        return _error(502, "Failed to retrieve session history", "HISTORY_FAILED")
    if isinstance(snapshots, dict) and "error" in snapshots:
        return _error(502, "Failed to retrieve session history", "HISTORY_FAILED")
    return {"snapshots": snapshots}


@router.post("/{session_id}/export/drive", response_model=None)
@limiter.limit(settings.rate_limit_post)
async def export_to_drive(
    request: Request,
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str] | JSONResponse:
    rewrite = await _get_latest(db, RewriteResult, session_id)
    if rewrite is None:
        return _error(404, "Rewrite not found", "REWRITE_NOT_FOUND")
    roadmap = await _get_latest(db, RoadmapResult, session_id)
    try:
        url = await invoke(
            "export_to_drive",
            rewritten_text=rewrite.rewritten_text,
            roadmap=roadmap.result_json if roadmap else {},
            session_id=str(session_id),
        )
    except Exception as exc:
        logger.error("Google Drive export failed: %s", exc)
        return _error(502, "Failed to export to Google Drive", "DRIVE_EXPORT_FAILED")
    if isinstance(url, dict) and "error" in url:
        return _error(502, "Failed to export to Google Drive", "DRIVE_EXPORT_FAILED")
    return {"drive_url": str(url)}


# ---------------------------------------------------------------------------
# 4.1 — SSE Streaming Progress for Analysis
# ---------------------------------------------------------------------------


@router.get("/{session_id}/analyze/stream")
async def stream_analysis(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Server-Sent Events stream for real-time analysis progress.
    Emits: step_start, step_done, complete, error events.
    """
    session = await _get_session(db, session_id)
    if session is None:
        return _error(404, "Session not found", "SESSION_NOT_FOUND")

    async def event_generator():
        steps = [
            ("extract",   "Extracting resume content…"),
            ("structure", "Parsing resume structure…"),
            ("ats",       "Running ATS compatibility check…"),
            ("score",     "Scoring 7 dimensions…"),
            ("insights",  "Generating actionable insights…"),
            ("finalize",  "Finalising analysis report…"),
        ]

        def sse(event: str, data: dict) -> str:
            return f"event: {event}\ndata: {json.dumps(data)}\n\n"

        try:
            for key, label in steps[:-1]:
                yield sse("step_start", {"step": key, "label": label})
                await asyncio.sleep(0)  # yield control

            # Kick off the real analysis
            yield sse("step_start", {"step": "finalize", "label": steps[-1][1]})
            result = await invoke(
                "analyze",
                raw_text=session.raw_text,
                target_role=None,
                job_description=None,
            )

            # Persist result
            if isinstance(result, dict) and "error" not in result:
                mode = result.get("mode")
                score = result.get("overall_score")
                if mode in {"general", "fresher"} and isinstance(score, int) and 0 <= score <= 100:
                    record = AnalysisResult(
                        session_id=session_id,
                        mode=mode,
                        overall_score=score,
                        result_json=result,
                    )
                    if not await _store(db, record):
                        pass  # stored successfully

            yield sse("complete", {"overall_score": result.get("overall_score") if isinstance(result, dict) else None})

        except Exception as exc:
            logger.error("SSE analysis failed: %s", exc, exc_info=True)
            yield sse("error", {"message": str(exc), "code": "ANALYSIS_FAILED"})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# 4.3 — Cover Letter Generator
# ---------------------------------------------------------------------------


class CoverLetterRequest(BaseModel):
    target_role: str
    company_name: str
    tone: str = "professional"  # professional | friendly | concise


@router.post("/{session_id}/cover-letter", response_model=None)
@limiter.limit(settings.rate_limit_post)
async def generate_cover_letter(
    request: Request,
    session_id: UUID,
    body: CoverLetterRequest,
    db: AsyncSession = Depends(get_db),
) -> dict | JSONResponse:
    """
    Generate a tailored cover letter using the resume text + any stored
    company research from this session.
    """
    session = await _get_session(db, session_id)
    if session is None:
        return _error(404, "Session not found", "SESSION_NOT_FOUND")

    company = await _get_latest(db, CompanyResult, session_id)
    analysis = await _get_latest(db, AnalysisResult, session_id)

    try:
        result = await invoke(
            "cover_letter",
            raw_text=session.raw_text,
            target_role=sanitize_text_input(body.target_role),
            company_name=sanitize_text_input(body.company_name),
            tone=body.tone,
            analysis=analysis.result_json if analysis else None,
            company_signals=company.result_json.get("company_signals") if company else None,
        )
    except Exception as exc:
        logger.error("Cover letter generation failed: %s", exc, exc_info=True)
        return _error(502, str(exc), "COVER_LETTER_FAILED")

    if isinstance(result, dict) and "error" in result:
        return _error(502, result.get("reason", "Cover letter generation failed"), "COVER_LETTER_FAILED")

    return result  # { "cover_letter_text": str, "word_count": int, "key_selling_points": [...] }


# ---------------------------------------------------------------------------
# 4.4 — Job Posting URL Analyzer
# ---------------------------------------------------------------------------


class JDUrlRequest(BaseModel):
    job_url: HttpUrl
    target_role: str | None = None


@router.post("/{session_id}/analyze/jd-url", response_model=None)
@limiter.limit(settings.rate_limit_post)
async def analyze_against_jd_url(
    request: Request,
    session_id: UUID,
    body: JDUrlRequest,
    db: AsyncSession = Depends(get_db),
) -> dict | JSONResponse:
    """
    1. Use Gemini search grounding to extract JD requirements from the URL.
    2. Re-run resume analysis graded against those requirements.
    Returns: standard analysis response PLUS `jd_keyword_gaps` and `jd_match_score`.
    """
    session = await _get_session(db, session_id)
    if session is None:
        return _error(404, "Session not found", "SESSION_NOT_FOUND")

    try:
        # Step 1: Extract JD content via search grounding
        jd_content = await invoke(
            "extract_jd",
            job_url=str(body.job_url),
        )
        if isinstance(jd_content, dict) and "error" in jd_content:
            return _error(502, "Failed to extract job description", "JD_EXTRACT_FAILED")

        # Step 2: Run analysis with JD context
        result = await invoke(
            "analyze",
            raw_text=session.raw_text,
            target_role=sanitize_text_input(body.target_role) or None,
            job_description=jd_content.get("extracted_text", ""),
        )
    except Exception as exc:
        logger.error("JD URL analysis failed: %s", exc, exc_info=True)
        return _error(502, str(exc), "JD_ANALYSIS_FAILED")

    if isinstance(result, dict) and "error" in result:
        return _error(502, result.get("reason", "JD analysis failed"), "JD_ANALYSIS_FAILED")

    # Persist as a regular analysis result
    mode = result.get("mode")
    score = result.get("overall_score")
    if mode in {"general", "fresher"} and isinstance(score, int) and 0 <= score <= 100:
        record = AnalysisResult(
            session_id=session_id,
            mode=mode,
            overall_score=score,
            target_role=sanitize_text_input(body.target_role),
            result_json=result,
        )
        if error := await _store(db, record):
            return error

    return result
