"""
Book routes - FastAPI route handlers.
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from app.database import get_db
from app.features.books.schemas import (
    BookCreate,
    BookUpdate,
    BookResponse,
    BookListResponse,
)
from app.features.auth.schemas import UserResponse
from app.features.auth.routes import get_current_user
from app.features.books.service import BookService

router = APIRouter()


@router.get("", response_model=BookListResponse)
async def get_books(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    type: Optional[str] = Query(None),
    condition: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    min_price: Optional[Decimal] = Query(None, ge=0),
    max_price: Optional[Decimal] = Query(None, ge=0),
    sort_by: Optional[str] = Query(None),
    sort_order: Optional[str] = Query("ASC", pattern="^(ASC|DESC)$"),
    db: AsyncSession = Depends(get_db),
) -> BookListResponse:
    """Get paginated list of books with filtering and sorting."""
    result = await BookService.get_books(
        db=db,
        page=page,
        limit=limit,
        type=type,
        condition=condition,
        search=search,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return result


@router.get("/my-books", response_model=BookListResponse)
async def get_my_books(
    page: int = Query(1, ge=1),
    limit: int = Query(1000, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> BookListResponse:
    """Get current user's books."""
    result = await BookService.get_my_books(
        db=db,
        seller_id=current_user.id,
        page=page,
        limit=limit,
    )
    return result


@router.get("/{book_id}", response_model=BookResponse)
async def get_book_by_id(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> BookResponse:
    """Get a book by ID."""
    book = await BookService.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )
    return BookResponse.model_validate(book)


@router.post(
    "", response_model=BookResponse, status_code=status.HTTP_201_CREATED
)
async def create_book(
    book_data: BookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> BookResponse:
    """Create a new book."""
    book = await BookService.create_book(
        db=db,
        book_data=book_data,
        seller_id=current_user.id,
    )
    return BookResponse.model_validate(book)


@router.put("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: UUID,
    book_data: BookUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> BookResponse:
    """Update a book."""
    book = await BookService.update_book(
        db=db,
        book_id=book_id,
        seller_id=current_user.id,
        book_data=book_data,
    )
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found or you do not have permission to update it",
        )
    return BookResponse.model_validate(book)


@router.delete("/{book_id}", status_code=status.HTTP_200_OK)
async def delete_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> dict:
    """Delete a book."""
    deleted = await BookService.delete_book(
        db=db,
        book_id=book_id,
        seller_id=current_user.id,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found or you do not have permission to delete it",
        )
    return {"message": "Book deleted successfully"}
