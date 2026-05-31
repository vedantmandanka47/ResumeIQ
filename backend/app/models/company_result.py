"""Company-specific analysis result model."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CompanyResult(Base):
    __tablename__ = "company_results"
    __table_args__ = (
        CheckConstraint("verdict IN ('GO', 'HOLD', 'REWORK')", name="ck_company_verdict"),
        Index("idx_company_session", "session_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_sessions.id", ondelete="CASCADE"), nullable=False
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    verdict: Mapped[str] = mapped_column(String(10), nullable=False)
    result_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped["ResumeSession"] = relationship(back_populates="company_results")
