"""
User routes - FastAPI route handlers.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.features.user.schemas import UserUpdate, UserProfileResponse
from app.features.auth.schemas import UserResponse
from app.features.auth.routes import get_current_user
from app.features.user.service import UserService

router = APIRouter()


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """Get current user profile."""
    user = await UserService.get_user_by_id(db, current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserProfileResponse.model_validate(user)


@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(
    update_data: UserUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """Update current user profile."""
    user = await UserService.update_user(db, current_user.id, update_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserProfileResponse.model_validate(user)


@router.put("/role", response_model=UserProfileResponse)
async def update_role(
    role_data: dict,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """Update user role."""
    role = role_data.get("role")
    if not role or role not in ["buyer", "seller", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid role (buyer, seller, or admin) is required",
        )

    update_data = UserUpdate(role=role)  # type: ignore[call-arg]
    user = await UserService.update_user(db, current_user.id, update_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserProfileResponse.model_validate(user)
