"""
ResumeIQ — SQLAlchemy Models Package
Import all model classes here so Alembic's env.py sees them
when it calls `Base.metadata.create_all()`.
"""

from app.database import Base          # re-export for convenience
from app.models.session import ResumeSession, AnalysisResult, RewriteResult  # noqa: F401
