"""Upload and session response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UploadResponse(BaseModel):
    session_id: UUID
    preview: str
    char_count: int
    filename: str


class SessionResponse(BaseModel):
    session_id: UUID
    filename: str
    char_count: int
    file_type: str
    created_at: datetime
