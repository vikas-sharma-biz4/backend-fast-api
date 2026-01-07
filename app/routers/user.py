"""
User routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.schemas.auth import UserResponse
from app.routers.auth import get_current_user
from app.models.user import User

router = APIRouter()


class RoleUpdate(BaseModel):
    """Role update request body."""
    role: str


@router.put("/role", response_model=UserResponse)
async def update_user_role(
    role_data: RoleUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Update user role.
    """
    role = role_data.role
    
    if role not in ["buyer", "seller", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be one of: buyer, seller, admin",
        )
    
    # Get user from database
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Update role
    user.role = role
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)

