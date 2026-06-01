"""Create the initial ResumeIQ schema.

Revision ID: 0001
Revises:
Create Date: 2026-06-01
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "resume_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=10), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("char_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("file_type IN ('pdf', 'docx')", name="ck_session_file_type"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "analysis_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("target_role", sa.String(length=255), nullable=True),
        sa.Column("result_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("mode IN ('general', 'fresher')", name="ck_analysis_mode"),
        sa.CheckConstraint("overall_score BETWEEN 0 AND 100", name="ck_analysis_score"),
        sa.ForeignKeyConstraint(["session_id"], ["resume_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "company_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("verdict", sa.String(length=10), nullable=False),
        sa.Column("result_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("verdict IN ('GO', 'HOLD', 'REWORK')", name="ck_company_verdict"),
        sa.ForeignKeyConstraint(["session_id"], ["resume_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "rewrite_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("rewritten_text", sa.Text(), nullable=False),
        sa.Column("changes_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("authenticity_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("pass1_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pass2_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["resume_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "roadmap_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("result_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["resume_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_analysis_session", "analysis_results", ["session_id", sa.text("created_at DESC")])
    op.create_index("idx_company_session", "company_results", ["session_id", sa.text("created_at DESC")])
    op.create_index("idx_rewrite_session", "rewrite_results", ["session_id", sa.text("created_at DESC")])
    op.create_index("idx_roadmap_session", "roadmap_results", ["session_id", sa.text("created_at DESC")])


def downgrade() -> None:
    op.drop_index("idx_roadmap_session", table_name="roadmap_results")
    op.drop_index("idx_rewrite_session", table_name="rewrite_results")
    op.drop_index("idx_company_session", table_name="company_results")
    op.drop_index("idx_analysis_session", table_name="analysis_results")
    op.drop_table("roadmap_results")
    op.drop_table("rewrite_results")
    op.drop_table("company_results")
    op.drop_table("analysis_results")
    op.drop_table("resume_sessions")
