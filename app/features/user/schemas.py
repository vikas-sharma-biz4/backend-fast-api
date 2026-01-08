"""
User schemas - Pydantic models for request/response validation.
"""
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    name: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[EmailStr] = None
    role: Optional[str] = Field(None, pattern="^(buyer|seller|admin)$")


class UserProfileResponse(BaseModel):
    """User profile response schema."""

    id: UUID
    name: str
    email: str
    role: str
    profile_picture_url: Optional[str] = None

    class Config:
        from_attributes = True
