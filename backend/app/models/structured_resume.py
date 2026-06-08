"""Cached canonical structured resume data keyed by resume content hash."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StructuredResume(Base):
    __tablename__ = "structured_resumes"
    __table_args__ = (Index("idx_structured_resume_hash", "resume_hash", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    structured_resume_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    active_template: Mapped[str] = mapped_column(String(120), nullable=False, default="minimalist")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    generated_resumes: Mapped[list["GeneratedResume"]] = relationship(
        back_populates="structured_resume", cascade="all, delete-orphan"
    )
