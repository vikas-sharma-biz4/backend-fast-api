"""
Authentication schemas - Pydantic models for request/response validation.
"""
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """Token response schema."""

    access_token: str
    token_type: str = "bearer"


class UserLogin(BaseModel):
    """User login schema."""

    email: EmailStr
    password: str = Field(..., min_length=6)


class UserSignup(BaseModel):
    """User signup schema."""

    name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str = Field(default="buyer", pattern="^(buyer|seller|admin)$")


class UserResponse(BaseModel):
    """User response schema."""

    id: UUID
    name: str
    email: str
    role: str
    profile_picture_url: str | None = None

    class Config:
        from_attributes = True
