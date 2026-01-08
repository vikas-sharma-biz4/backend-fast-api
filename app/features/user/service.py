"""
User service - business logic layer.
"""
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.features.user.schemas import UserUpdate


class UserService:
    """Service for user-related operations."""

    @staticmethod
    async def get_user_by_id(
        db: AsyncSession, user_id: UUID
    ) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_user(
        db: AsyncSession, user_id: UUID, update_data: UserUpdate
    ) -> Optional[User]:
        """Update user profile."""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(user, field, value)

        await db.flush()
        await db.refresh(user)
        await db.commit()

        return user

    @staticmethod
    async def update_user_profile_picture(
        db: AsyncSession, user_id: UUID, profile_picture_url: str
    ) -> Optional[User]:
        """Update user profile picture."""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return None

        user.profile_picture_url = profile_picture_url
        await db.flush()
        await db.refresh(user)
        await db.commit()

        return user
