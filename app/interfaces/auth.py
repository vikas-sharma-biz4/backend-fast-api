"""
Authentication-related type interfaces.
"""
from typing import Literal, Optional
from datetime import datetime
from uuid import UUID
from dataclasses import dataclass


UserRole = Literal["buyer", "seller", "admin"]


class UserAttributes:
    """User attributes interface."""

    id: UUID
    name: str
    email: str
    password: Optional[str]
    reset_token: Optional[str]
    reset_token_expiry: Optional[datetime]
    otp: Optional[str]
    otp_expiry: Optional[datetime]
    google_id: Optional[str]
    profile_picture_url: Optional[str]
    role: UserRole
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class UserPublic:
    """Public user data (without sensitive information)."""

    id: UUID
    name: str
    email: str
    profile_picture_url: Optional[str]
    role: UserRole
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class UserCreationAttributes:
    """Attributes for creating a new user."""

    name: str
    email: str
    password: Optional[str]
    google_id: Optional[str]
    role: Optional[UserRole]


class UserUpdateAttributes:
    """Attributes for updating a user."""

    name: Optional[str]
    email: Optional[str]
    password: Optional[str]
    reset_token: Optional[str]
    reset_token_expiry: Optional[datetime]
    otp: Optional[str]
    otp_expiry: Optional[datetime]
    google_id: Optional[str]
    profile_picture_url: Optional[str]
    role: Optional[UserRole]


class OTPVerificationResult:
    """Result of OTP verification."""

    valid: bool
    message: Optional[str]
    user_id: Optional[UUID]
    user: Optional[UserAttributes]


class JWTPayload:
    """JWT token payload."""

    user_id: UUID


@dataclass
class EmailResult:
    """Result of email sending operation."""

    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class AuthResponse:
    """Authentication response."""

    message: str
    token: str
    user: UserPublic


class ApiResponse:
    """Generic API response."""

    message: str
    data: Optional[dict]
