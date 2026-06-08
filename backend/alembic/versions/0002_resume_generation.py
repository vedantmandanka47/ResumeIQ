"""Add structured resume cache and generated file records.

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "structured_resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("resume_hash", sa.String(length=64), nullable=False),
        sa.Column("structured_resume_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("active_template", sa.String(length=120), nullable=False, server_default="minimalist"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("resume_hash"),
    )
    op.create_index("idx_structured_resume_hash", "structured_resumes", ["resume_hash"], unique=True)

    op.create_table(
        "generated_resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("structured_resume_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_id", sa.String(length=120), nullable=False),
        sa.Column("docx_path", sa.Text(), nullable=False),
        sa.Column("pdf_path", sa.Text(), nullable=True),
        sa.Column("pdf_error", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["resume_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["structured_resume_id"], ["structured_resumes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_generated_resume_session", "generated_resumes", ["session_id", sa.text("created_at DESC")])
    op.create_index("idx_generated_resume_expires", "generated_resumes", ["expires_at"])


def downgrade() -> None:
    op.drop_index("idx_generated_resume_expires", table_name="generated_resumes")
    op.drop_index("idx_generated_resume_session", table_name="generated_resumes")
    op.drop_table("generated_resumes")
    op.drop_index("idx_structured_resume_hash", table_name="structured_resumes")
    op.drop_table("structured_resumes")
