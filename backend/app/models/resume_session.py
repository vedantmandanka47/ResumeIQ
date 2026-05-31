"""Uploaded resume session model."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ResumeSession(Base):
    __tablename__ = "resume_sessions"
    __table_args__ = (CheckConstraint("file_type IN ('pdf', 'docx')", name="ck_session_file_type"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    analyses: Mapped[list["AnalysisResult"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    company_results: Mapped[list["CompanyResult"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    rewrites: Mapped[list["RewriteResult"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    roadmaps: Mapped[list["RoadmapResult"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
