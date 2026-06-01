"""Resume upload, analysis, rewrite, persistence, and export endpoints."""

import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
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
)
from app.schemas.analysis import AnalysisRequest
from app.schemas.company import CompanyAnalysisRequest
from app.schemas.rewrite import RewriteRequest
from app.schemas.upload import SessionResponse, UploadResponse
from app.services.agent_gateway import invoke
from app.services.parser import extract_text_from_docx, extract_text_from_pdf

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/resume", tags=["resume"])


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
    """Store one record in an explicit write transaction."""
    try:
        if db.in_transaction():
            await db.rollback()
        async with db.begin():
            db.add(record)
            await db.flush()
        return None
    except SQLAlchemyError as exc:
        logger.error("Database write failed for %s: %s", type(record).__name__, exc, exc_info=True)
        return _error(503, "Database write failed", "DATABASE_WRITE_FAILED")


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
) -> AnalysisResult | JSONResponse:
    try:
        result = await invoke("analyze", raw_text=session.raw_text, target_role=target_role)
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
    record = await _run_and_store_analysis(db, session, target_role)
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
