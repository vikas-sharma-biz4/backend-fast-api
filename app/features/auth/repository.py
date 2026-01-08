"""
Authentication repository - data access layer.
"""
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User


class AuthRepository:
    """Repository for authentication data access."""

    @staticmethod
    async def get_user_by_email(
        db: AsyncSession, email: str
    ) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_id(
        db: AsyncSession, user_id: UUID
    ) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_google_id(
        db: AsyncSession, google_id: str
    ) -> Optional[User]:
        """Get user by Google ID."""
        result = await db.execute(
            select(User).where(User.google_id == google_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(
        db: AsyncSession,
        name: str,
        email: str,
        hashed_password: str,
        role: str = "buyer",
    ) -> User:
        """Create a new user."""
        user = User(
            name=name,
            email=email,
            password=hashed_password,
            role=role,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        await db.commit()
        return user

    @staticmethod
    async def create_oauth_user(
        db: AsyncSession,
        name: str,
        email: str,
        google_id: str,
        role: str = "buyer",
    ) -> User:
        """Create a new OAuth user."""
        user = User(
            name=name,
            email=email,
            password=None,
            role=role,
            google_id=google_id,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        await db.commit()
        return user

    @staticmethod
    async def update_user_google_id(
        db: AsyncSession, user: User, google_id: str
    ) -> User:
        """Update user's Google ID."""
        user.google_id = google_id
        await db.flush()
        await db.refresh(user)
        await db.commit()
        return user
