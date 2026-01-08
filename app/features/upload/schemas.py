"""
Upload schemas - Pydantic models for request/response validation.
"""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class FileResponse(BaseModel):
    """File upload response schema."""

    id: UUID
    filename: str
    original_name: str
    mime_type: str
    size: int
    url: str
    created_at: datetime

    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    """File list response schema."""

    files: list[FileResponse]
