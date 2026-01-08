"""
User model.
"""
from sqlalchemy import String, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid
from typing import Literal, Optional

from app.database import Base
from app.models.base import TimestampMixin


RoleType = Literal["buyer", "seller", "admin"]


class User(Base, TimestampMixin):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(
        SQLEnum("buyer", "seller", "admin", name="user_role"),
        nullable=False,
        default="buyer",
    )
    google_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    profile_picture_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
