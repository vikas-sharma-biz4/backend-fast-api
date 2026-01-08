"""
Authentication service - business logic layer.
"""
from datetime import datetime, timedelta
from uuid import UUID
from typing import Optional, Tuple
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.features.auth.repository import AuthRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for authentication business logic."""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(
        data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    async def get_user_by_email(
        db: AsyncSession, email: str
    ) -> Optional[User]:
        """Get user by email."""
        return await AuthRepository.get_user_by_email(db, email)

    @staticmethod
    async def get_user_by_id(
        db: AsyncSession, user_id: UUID
    ) -> Optional[User]:
        """Get user by ID."""
        return await AuthRepository.get_user_by_id(db, user_id)

    @staticmethod
    async def create_user(
        db: AsyncSession,
        name: str,
        email: str,
        password: str,
        role: str = "buyer",
    ) -> User:
        """Create a new user."""
        hashed_password = AuthService.get_password_hash(password)
        return await AuthRepository.create_user(
            db, name, email, hashed_password, role
        )

    @staticmethod
    async def authenticate_user(
        db: AsyncSession, email: str, password: str
    ) -> Optional[User]:
        """Authenticate a user."""
        user = await AuthRepository.get_user_by_email(db, email)
        if not user:
            return None
        if not user.password:
            return None
        if not AuthService.verify_password(password, user.password):
            return None
        return user

    @staticmethod
    async def create_or_update_oauth_user(
        db: AsyncSession,
        google_id: str,
        email: str,
        name: str,
    ) -> Tuple[User, bool]:
        """
        Create or update user from Google OAuth.

        Returns:
            Tuple of (user, is_new_user)
        """
        # Check if user exists with this Google ID
        user = await AuthRepository.get_user_by_google_id(db, google_id)
        if user:
            return user, False

        # Check if user exists with this email
        existing_user = await AuthRepository.get_user_by_email(db, email)
        if existing_user:
            # Update existing user with Google ID
            return (
                await AuthRepository.update_user_google_id(
                    db, existing_user, google_id
                ),
                False,
            )

        # Create new user
        new_user = await AuthRepository.create_oauth_user(
            db, name, email, google_id
        )
        return new_user, True
