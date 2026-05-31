"""Two-pass rewritten resume result model."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RewriteResult(Base):
    __tablename__ = "rewrite_results"
    __table_args__ = (Index("idx_rewrite_session", "session_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_sessions.id", ondelete="CASCADE"), nullable=False
    )
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    rewritten_text: Mapped[str] = mapped_column(Text, nullable=False)
    changes_json: Mapped[Any] = mapped_column(JSONB, nullable=False)
    authenticity_json: Mapped[Any] = mapped_column(JSONB, nullable=False)
    pass1_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pass2_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped["ResumeSession"] = relationship(back_populates="rewrites")
