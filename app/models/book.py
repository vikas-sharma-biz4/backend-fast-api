"""
Book model.
"""
from sqlalchemy import String, Numeric, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal
import uuid
from typing import Literal, Optional

from app.database import Base
from typing import TYPE_CHECKING

from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


BookType = Literal["fiction", "non-fiction", "academic", "biography", "other"]
BookCondition = Literal["new", "like-new", "good", "fair", "poor"]


class Book(Base, TimestampMixin):
    """Book model for the marketplace."""

    __tablename__ = "books"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    isbn: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    type: Mapped[str] = mapped_column(
        SQLEnum("fiction", "non-fiction", "academic", "biography", "other", name="book_type"),
        nullable=False,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    seller_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    condition: Mapped[str] = mapped_column(
        SQLEnum("new", "like-new", "good", "fair", "poor", name="book_condition"),
        nullable=False,
        default="good",
    )
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationship
    seller: Mapped["User"] = relationship("User", backref="books")
