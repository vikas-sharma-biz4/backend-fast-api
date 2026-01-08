"""
Book-related type interfaces.
"""
from typing import Literal, Optional
from decimal import Decimal
from uuid import UUID
from datetime import datetime


BookType = Literal["fiction", "non-fiction", "academic", "biography", "other"]
BookCondition = Literal["new", "like-new", "good", "fair", "poor"]


class BookAttributes:
    """Book attributes interface."""

    id: UUID
    title: str
    author: str
    isbn: Optional[str]
    type: BookType
    price: Decimal
    description: Optional[str]
    seller_id: UUID
    condition: BookCondition
    image_url: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class BookCreationAttributes:
    """Attributes for creating a new book."""

    title: str
    author: str
    isbn: Optional[str]
    type: BookType
    price: Decimal
    description: Optional[str]
    seller_id: UUID
    condition: BookCondition
    image_url: Optional[str]


class BookUpdateAttributes:
    """Attributes for updating a book."""

    title: Optional[str]
    author: Optional[str]
    isbn: Optional[str]
    type: Optional[BookType]
    price: Optional[Decimal]
    description: Optional[str]
    condition: Optional[BookCondition]
    image_url: Optional[str]
