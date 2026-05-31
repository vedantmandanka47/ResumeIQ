"""Import all models so Alembic can discover the complete schema."""

from app.database import Base
from app.models.analysis_result import AnalysisResult
from app.models.company_result import CompanyResult
from app.models.resume_session import ResumeSession
from app.models.rewrite_result import RewriteResult
from app.models.roadmap_result import RoadmapResult

__all__ = [
    "Base",
    "ResumeSession",
    "AnalysisResult",
    "CompanyResult",
    "RewriteResult",
    "RoadmapResult",
]
