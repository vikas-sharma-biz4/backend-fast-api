"""
Core dependencies for FastAPI routes.
Shared dependencies like authentication.
"""
from fastapi import Depends
from app.features.auth.routes import get_current_user
from app.features.auth.schemas import UserResponse

# Re-export for convenience
__all__ = ["get_current_user", "UserResponse"]
