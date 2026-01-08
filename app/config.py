"""
Application configuration using Pydantic settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    """Application settings with type validation."""

    # App
    APP_NAME: str = "Auth Module"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/auth_module_dev"

    # JWT
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_EXPIRES_IN: str = "7d"

    # Email
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_SECURE: bool = False
    EMAIL_USER: str = ""
    EMAIL_PASSWORD: str = ""

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_CALLBACK_URL: str = "http://localhost:8000/api/auth/google/callback"
    FRONTEND_URL: str = "http://localhost:3000"

    @field_validator("FRONTEND_URL")
    @classmethod
    def clean_frontend_url(cls, v: str) -> str:
        """Clean FRONTEND_URL - remove trailing slashes and invalid characters."""
        if not v:
            return v
        # Remove trailing 's' if present (common typo: localhost:3000s)
        v = v.rstrip("s")
        # Remove trailing slashes
        v = v.rstrip("/")
        # Strip whitespace
        v = v.strip()
        return v

    @field_validator("GOOGLE_CALLBACK_URL")
    @classmethod
    def clean_callback_url(cls, v: str) -> str:
        """Clean GOOGLE_CALLBACK_URL - remove trailing whitespace."""
        if not v:
            return v
        return v.strip()

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",  # Ignore extra fields from .env that aren't defined in the model
    )


settings = Settings()
