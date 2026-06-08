"""Analysis request schemas."""

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    target_role: str | None = Field(default=None, max_length=2000)
    job_description: str | None = Field(default=None, max_length=10000)
