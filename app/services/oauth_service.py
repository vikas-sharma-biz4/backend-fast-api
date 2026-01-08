"""
Google OAuth service.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.services.auth_service import (
    get_user_by_email,
    create_user,
    get_password_hash,
)


async def get_user_by_google_id(
    db: AsyncSession, google_id: str
) -> Optional[User]:
    """Get user by Google ID."""
    result = await db.execute(select(User).where(User.google_id == google_id))
    return result.scalar_one_or_none()


async def create_or_update_oauth_user(
    db: AsyncSession,
    google_id: str,
    email: str,
    name: str,
) -> tuple[User, bool]:
    """
    Create or update user from Google OAuth.

    Returns:
        Tuple of (user, is_new_user)
    """
    # Check if user exists with this Google ID
    user = await get_user_by_google_id(db, google_id)
    if user:
        return user, False

    # Check if user exists with this email
    existing_user = await get_user_by_email(db, email)
    if existing_user:
        # Update existing user with Google ID
        existing_user.google_id = google_id
        await db.flush()  # Flush changes
        await db.refresh(existing_user)  # Refresh to get updated timestamps
        await db.commit()
        return existing_user, False

    # Create new user (OAuth users don't have passwords)
    user = User(
        name=name,
        email=email,
        password=None,  # OAuth users don't have passwords
        role="buyer",  # Default role
        google_id=google_id,
    )

    db.add(user)
    await db.flush()  # Flush to get the ID without committing
    await db.refresh(user)  # Refresh to get all computed fields (timestamps)
    await db.commit()

    return user, True
