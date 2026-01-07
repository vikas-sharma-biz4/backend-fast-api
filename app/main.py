"""
FastAPI main application entry point.
Demonstrates event loop concepts and async/await patterns.
"""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, init_db
from app.routers import books, auth, user
from app.utils.background_tasks import BackgroundTaskManager
from app.utils.decorators import log_execution_time


# Event loop lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for FastAPI.
    Demonstrates event loop lifecycle management.
    """
    # Startup: Initialize database and background tasks
    print("🚀 Starting up FastAPI application...")
    print(f"📊 Event loop: {asyncio.get_event_loop()}")
    print(f"🔄 Is event loop running: {asyncio.get_event_loop().is_running()}")
    
    # Initialize database (gracefully handle connection errors)
    try:
        await init_db()
    except asyncio.CancelledError:
        # Handle cancellation during reload
        raise
    except Exception as e:
        print(f"⚠️  Database initialization error: {e}")
        print("⚠️  Continuing startup without database initialization...")
    
    # Start background task manager
    try:
        task_manager = BackgroundTaskManager()
        app.state.background_task_manager = task_manager
        asyncio.create_task(task_manager.start())
    except Exception as e:
        print(f"⚠️  Background task manager error: {e}")
    
    print("✅ Application started successfully")
    
    yield
    
    # Shutdown: Clean up resources
    print("🛑 Shutting down FastAPI application...")
    try:
        if hasattr(app.state, "background_task_manager"):
            await app.state.background_task_manager.stop()
    except asyncio.CancelledError:
        # Expected during reload, suppress error
        pass
    except Exception as e:
        print(f"⚠️  Error during shutdown: {e}")
    print("✅ Application shut down successfully")


@log_execution_time
def create_app() -> FastAPI:
    """
    Factory function to create and configure FastAPI application.
    Demonstrates decorator usage for logging execution time.
    """
    app = FastAPI(
        title="Book Marketplace API",
        description="FastAPI backend with async operations and type checking",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(books.router, prefix="/api/books", tags=["books"])
    app.include_router(user.router, prefix="/api/user", tags=["user"])
    
    @app.get("/")
    @log_execution_time
    async def root() -> dict[str, str]:
        """
        Root endpoint demonstrating async function and decorator.
        """
        return {
            "message": "Welcome to Book Marketplace API",
            "version": "1.0.0",
            "event_loop_info": {
                "is_running": asyncio.get_event_loop().is_running(),
            },
        }
    
    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy"}
    
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

