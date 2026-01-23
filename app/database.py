"""
Database connection and session management.
Demonstrates async SQLAlchemy usage.
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import event
from sqlalchemy.exc import OperationalError
from typing import AsyncGenerator

from app.config import settings

logger = logging.getLogger(__name__)

# Convert postgresql:// to postgresql+asyncpg:// for async support
database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    database_url,
    echo=settings.ENVIRONMENT == "development",
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session with deadlock handling.
    Demonstrates async generator pattern and retry logic for deadlocks.
    """
    max_retries = 3
    retry_delay = 0.1  # seconds

    for attempt in range(max_retries):
        async with AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
                break
            except OperationalError as e:
                error_str = str(e).lower()
                # Check for deadlock-related errors
                if "deadlock" in error_str or "lock" in error_str:
                    await session.rollback()
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(
                            f"Deadlock detected (attempt {attempt + 1}/{max_retries}). "
                            f"Retrying after {wait_time}s..."
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Deadlock retry exhausted after {max_retries} attempts")
                        raise
                else:
                    await session.rollback()
                    raise
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


async def init_db() -> None:
    """
    Initialize database tables.
    Gracefully handles connection errors and cancellation.
    """
    try:
        from app.models import book, user  # noqa: F401

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables initialized successfully")
    except asyncio.CancelledError:
        # Handle cancellation during reload - this is expected
        raise
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize database: {e}")
        print("⚠️  The application will continue, but database operations may fail.")
        print("⚠️  Please check your DATABASE_URL in .env file and ensure PostgreSQL is running.")
