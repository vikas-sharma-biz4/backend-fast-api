"""
Book Pydantic schemas for request/response validation.
Demonstrates type safety with Pydantic.
"""
from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal

from app.models.book import BookType, BookCondition


class BookBase(BaseModel):
    """Base book schema with common fields."""
    
    title: str = Field(..., min_length=1, max_length=255, description="Book title")
    author: str = Field(..., min_length=1, max_length=255, description="Author name")
    isbn: Optional[str] = Field(None, max_length=20, description="ISBN number")
    type: BookType = Field(..., description="Book type/category")
    price: Decimal = Field(..., gt=0, description="Book price")
    description: Optional[str] = Field(None, description="Book description")
    condition: BookCondition = Field(default="good", description="Book condition")
    image_url: Optional[str] = Field(None, max_length=500, description="Book image URL")
    
    @field_validator("price")
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        """Validate price is positive."""
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        return v


class BookCreate(BookBase):
    """Schema for creating a book."""
    pass


class BookUpdate(BaseModel):
    """Schema for updating a book (all fields optional)."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    author: Optional[str] = Field(None, min_length=1, max_length=255)
    isbn: Optional[str] = Field(None, max_length=20)
    type: Optional[BookType] = None
    price: Optional[Decimal] = Field(None, gt=0)
    description: Optional[str] = None
    condition: Optional[BookCondition] = None
    image_url: Optional[str] = Field(None, max_length=500)


class BookResponse(BookBase):
    """Schema for book response."""
    
    id: UUID
    seller_id: UUID
    created_at: datetime
    updated_at: datetime
    price: float = Field(..., gt=0, description="Book price")  # Override to use float instead of Decimal
    
    @field_validator("price", mode="before")
    @classmethod
    def convert_decimal_to_float(cls, v: Decimal | float | str) -> float:
        """Convert Decimal to float for JSON serialization."""
        if isinstance(v, Decimal):
            return float(v)
        if isinstance(v, str):
            return float(v)
        return float(v)
    
    class Config:
        from_attributes = True


class BookListResponse(BaseModel):
    """Schema for paginated book list response."""
    
    data: list[BookResponse]
    total: int
    page: int
    limit: int
    total_pages: int

