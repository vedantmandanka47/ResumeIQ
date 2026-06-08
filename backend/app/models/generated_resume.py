"""Generated resume artifact metadata."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class GeneratedResume(Base):
    __tablename__ = "generated_resumes"
    __table_args__ = (
        Index("idx_generated_resume_session", "session_id", "created_at"),
        Index("idx_generated_resume_expires", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_sessions.id", ondelete="CASCADE"), nullable=False
    )
    structured_resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("structured_resumes.id", ondelete="CASCADE"), nullable=False
    )
    template_id: Mapped[str] = mapped_column(String(120), nullable=False)
    docx_path: Mapped[str] = mapped_column(Text, nullable=False)
    pdf_path: Mapped[str | None] = mapped_column(Text)
    pdf_error: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped["ResumeSession"] = relationship(back_populates="generated_resumes")
    structured_resume: Mapped["StructuredResume"] = relationship(back_populates="generated_resumes")
