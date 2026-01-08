# FastAPI Backend

A complete FastAPI backend implementation demonstrating advanced Python concepts and async programming.

## Features

### Backend Concepts Demonstrated

1. **Event Loop Concepts**
   - Async/await patterns throughout
   - Event loop lifecycle management in `app/main.py`
   - Background tasks using asyncio

2. **Decorator for Logging Execution Times**
   - `@log_execution_time` decorator in `app/utils/decorators.py`
   - Works with both sync and async functions
   - Logs execution time and errors

3. **Generator for Reading Large Files**
   - `read_large_file_line_by_line()` in `app/utils/file_reader.py`
   - Memory-efficient line-by-line file reading
   - Async version available

4. **Async Background Tasks**
   - `BackgroundTaskManager` in `app/utils/background_tasks.py`
   - Periodic cleanup and health check tasks
   - Proper task lifecycle management

5. **Pyright Type Checking**
   - Configured in `pyrightconfig.json`
   - Full type annotations throughout
   - Type-safe database operations

6. **Full CRUD Functionality**
   - Complete CRUD operations for books
   - Pagination, filtering, and sorting
   - Authentication and authorization

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file (see `.env.example`):
```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/auth_module_dev
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

3. Run the application:
```bash
# Option 1: Using uvicorn directly (recommended)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Option 2: Using the run script
python run.py
```

4. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Type Checking

Run Pyright type checking:
```bash
pyright app
```

## API Endpoints

### Authentication
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user

### Books (CRUD)
- `GET /api/books` - Get paginated list of books (with filters)
- `GET /api/books/{book_id}` - Get book by ID
- `POST /api/books` - Create a new book (requires auth)
- `PUT /api/books/{book_id}` - Update a book (requires auth)
- `DELETE /api/books/{book_id}` - Delete a book (requires auth)
- `GET /api/books/my-books` - Get current user's books (requires auth)

## Architecture

- **Models**: SQLAlchemy models with async support
- **Schemas**: Pydantic models for validation
- **Services**: Business logic layer
- **Routers**: API endpoints
- **Utils**: Decorators, file readers, background tasks

## Database

Uses PostgreSQL with async SQLAlchemy. Make sure PostgreSQL is running and the database exists before starting the application.
