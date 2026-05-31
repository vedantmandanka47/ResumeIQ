"""
ResumeIQ — Core Database Models
Defines all PostgreSQL tables used by the application.

Schema overview:
  resume_sessions   — one row per uploaded resume; stores parsed text + metadata
  analysis_results  — one-to-one with a session; stores the full Gemini analysis JSON
  rewrite_results   — one-to-one with a session; stores the rewritten resume + changelog

Every table has:
  - id (UUID primary key)
  - created_at (server-side UTC timestamp, auto-set on INSERT)
  - updated_at (auto-updated on every UPDATE)
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow() -> datetime:
    """Returns the current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


# ============================================================
# resume_sessions
# ============================================================

class ResumeSession(Base):
    """
    Represents a single resume upload session.
    Created at upload time; referenced by all downstream results.
    """
    __tablename__ = "resume_sessions"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Unique session identifier returned to the frontend on upload",
    )

    # File metadata
    original_filename = Column(String(255), nullable=True)
    file_type         = Column(String(10),  nullable=True, comment="pdf or docx")
    file_size_bytes   = Column(BigInteger,  nullable=True)

    # Extracted content
    raw_text          = Column(Text, nullable=True, comment="Full parsed text from the resume file")
    extraction_notes  = Column(Text, nullable=True, comment="Warnings from the parser, e.g. low confidence")

    # Optional user-supplied context
    target_role       = Column(String(255), nullable=True)
    target_company    = Column(String(255), nullable=True)

    # Fresher flag — set by the analysis agent
    is_fresher        = Column(Boolean, nullable=True, default=None)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    # Relationships
    analysis = relationship("AnalysisResult", back_populates="session", uselist=False, cascade="all, delete-orphan")
    rewrite  = relationship("RewriteResult",  back_populates="session", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ResumeSession id={self.id} file={self.original_filename}>"


# ============================================================
# analysis_results
# ============================================================

class AnalysisResult(Base):
    """
    Stores the structured Gemini analysis for a resume session.
    The full JSON payload from the LLM is kept in `result_json`
    so the schema can evolve without migrations every phase.
    """
    __tablename__ = "analysis_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resume_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Denormalised top-level fields for fast queries
    overall_score = Column(Integer,     nullable=True)
    mode          = Column(String(20),  nullable=True, comment="general | fresher | company")

    # Full structured payload — JSONB for efficient querying in Postgres
    result_json   = Column(JSONB, nullable=True, comment="Full analysis output from the LLM")

    # Company-specific extension (Phase 3)
    company_json  = Column(JSONB, nullable=True, comment="Company intelligence + verdict payload")

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    # Relationship
    session = relationship("ResumeSession", back_populates="analysis")

    def __repr__(self) -> str:
        return f"<AnalysisResult session={self.session_id} score={self.overall_score}>"


# ============================================================
# rewrite_results
# ============================================================

class RewriteResult(Base):
    """
    Stores both passes of the resume rewrite pipeline (Phase 4):
      Pass 1 — the ATS-optimised rewrite
      Pass 2 — the authenticity-checked final version + change log
    """
    __tablename__ = "rewrite_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resume_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Pass 1 output
    rewrite_pass1 = Column(Text, nullable=True, comment="Raw rewrite output before authenticity check")

    # Pass 2 output — final deliverable
    rewrite_final = Column(Text, nullable=True, comment="Authenticity-checked final resume text")

    # Change log from Pass 2
    change_log_json = Column(JSONB, nullable=True, comment="List of changes made and why")

    # Timestamps — per pass so the UI can show when each ran
    pass1_at = Column(DateTime(timezone=True), nullable=True)
    pass2_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    # Relationship
    session = relationship("ResumeSession", back_populates="rewrite")

    def __repr__(self) -> str:
        return f"<RewriteResult session={self.session_id}>"
