"""Rewrite request schemas."""

from pydantic import BaseModel, Field


class RewriteRequest(BaseModel):
    target_role: str | None = Field(default=None, max_length=2000)
    company_name: str | None = Field(default=None, max_length=2000)
