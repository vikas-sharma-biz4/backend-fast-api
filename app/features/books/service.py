"""
Book service layer with business logic.
"""
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.orm import selectinload
from decimal import Decimal

from app.models.book import Book
from app.features.books.schemas import (
    BookCreate,
    BookUpdate,
    BookListResponse,
    BookResponse,
)
from app.utils.decorators import log_execution_time


class BookService:
    """Service for book-related operations."""

    @staticmethod
    @log_execution_time
    async def create_book(
        db: AsyncSession,
        book_data: BookCreate,
        seller_id: UUID,
    ) -> Book:
        """Create a new book."""
        book = Book(
            **book_data.model_dump(),
            seller_id=seller_id,
        )
        db.add(book)
        await db.flush()
        await db.refresh(book)
        await db.commit()
        return book

    @staticmethod
    @log_execution_time
    async def get_book_by_id(
        db: AsyncSession, book_id: UUID
    ) -> Optional[Book]:
        """Get a book by ID."""
        result = await db.execute(
            select(Book)
            .where(Book.id == book_id)
            .options(selectinload(Book.seller))
        )
        return result.scalar_one_or_none()

    @staticmethod
    @log_execution_time
    async def get_books(
        db: AsyncSession,
        page: int = 1,
        limit: int = 20,
        type: Optional[str] = None,
        condition: Optional[str] = None,
        search: Optional[str] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = "ASC",
    ) -> BookListResponse:
        """Get paginated list of books with filtering and sorting."""
        query = select(Book)
        conditions = []

        if type:
            conditions.append(Book.type == type)

        if condition:
            conditions.append(Book.condition == condition)

        if min_price is not None:
            conditions.append(Book.price >= min_price)

        if max_price is not None:
            conditions.append(Book.price <= max_price)

        if search:
            search_pattern = f"%{search}%"
            conditions.append(
                or_(
                    Book.title.ilike(search_pattern),
                    Book.author.ilike(search_pattern),
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        count_query = select(func.count(Book.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        if sort_by:
            sort_column = getattr(Book, sort_by, None)
            if sort_column:
                if sort_order and sort_order.upper() == "DESC":
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(Book.created_at.desc())

        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        books = result.scalars().all()

        total_pages = (total + limit - 1) // limit if total > 0 else 0

        return BookListResponse(
            data=[BookResponse.model_validate(book) for book in books],
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        )

    @staticmethod
    @log_execution_time
    async def update_book(
        db: AsyncSession,
        book_id: UUID,
        seller_id: UUID,
        book_data: BookUpdate,
    ) -> Optional[Book]:
        """Update a book."""
        result = await db.execute(
            select(Book).where(
                and_(Book.id == book_id, Book.seller_id == seller_id)
            )
        )
        book = result.scalar_one_or_none()

        if not book:
            return None

        update_data = book_data.model_dump(exclude_unset=True)

        if not update_data:
            return book

        set_clauses = []
        params = {"book_id": book_id, "seller_id": seller_id}

        for field, value in update_data.items():
            if value is not None:
                param_name = f"_{field}"
                params[param_name] = value

                if field in ("condition", "type"):
                    db_enum_type = (
                        "enum_books_condition"
                        if field == "condition"
                        else "enum_books_type"
                    )
                    set_clauses.append(
                        f"{field} = CAST(:{param_name} AS {db_enum_type})"
                    )
                else:
                    set_clauses.append(f"{field} = :{param_name}")

        if set_clauses:
            sql = text(
                f"UPDATE books SET {', '.join(set_clauses)}, "
                "updated_at = CURRENT_TIMESTAMP "
                "WHERE id = :book_id AND seller_id = :seller_id"
            )
            await db.execute(sql, params)
            await db.commit()
            await db.refresh(book)

        return book

    @staticmethod
    @log_execution_time
    async def delete_book(
        db: AsyncSession,
        book_id: UUID,
        seller_id: UUID,
    ) -> bool:
        """Delete a book."""
        result = await db.execute(
            select(Book).where(
                and_(Book.id == book_id, Book.seller_id == seller_id)
            )
        )
        book = result.scalar_one_or_none()

        if not book:
            return False

        await db.delete(book)
        await db.commit()
        return True

    @staticmethod
    @log_execution_time
    async def get_my_books(
        db: AsyncSession,
        seller_id: UUID,
        page: int = 1,
        limit: int = 1000,
    ) -> BookListResponse:
        """Get books by seller ID."""
        query = select(Book).where(Book.seller_id == seller_id)

        count_query = select(func.count(Book.id)).where(
            Book.seller_id == seller_id
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * limit
        query = (
            query.order_by(Book.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await db.execute(query)
        books = result.scalars().all()

        total_pages = (total + limit - 1) // limit if total > 0 else 0

        return BookListResponse(
            data=[BookResponse.model_validate(book) for book in books],
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        )
