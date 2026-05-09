# DryDocs Backend

> **FastAPI-based Document Management API**
>
> Secure document upload, storage, versioning, and Markdown conversion service.

---

## Key Design Decisions

### Architecture Pattern
- **Layered Architecture**: Routes → CRUD → Database/Storage
- **Separation of Concerns**: Each layer has a single responsibility
- **Dependency Injection**: FastAPI's `Depends` used for database sessions and authentication

### Database
- **Async SQLAlchemy 2.0**: Full async support with `asyncpg` driver
- **Centralized Session Management**: Single `get_db()` dependency in `database.py`, imported everywhere
- **Alembic Migrations**: Schema changes managed via proper migration system (not runtime ALTER TABLE)
- **Full-Text Search**: PostgreSQL `tsvector`/`tsquery` for efficient document search

### Security
- **JWT Authentication**: Integration with frontend's `better-auth` library
- **Type-Safe SQL**: SQLAlchemy ORM expressions to prevent SQL injection
- **Input Validation**: Pydantic v2 models for all request/response data

### Code Quality
- **Type Safety**: Mandatory type hints, checked with `ty`
- **Linting**: `ruff` for PEP 8 compliance and code quality
- **Testing**: Comprehensive mock-based tests with `pytest-asyncio`

---

## Overview

The DryDocs backend is a FastAPI application that provides a RESTful API for managing documents. It handles:

- **Document Upload**: Accept PDF and DOCX files with metadata
- **Version Control**: Automatic version tracking on each upload
- **Markdown Conversion**: Convert documents to Markdown using Pandoc
- **Object Storage**: Store files in MinIO (S3-compatible)
- **Metadata Storage**: Store document metadata in PostgreSQL
- **Validation**: Mark document versions as validated

### Request Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant MinIO
    participant PostgreSQL
    participant Pandoc
    
    Client->>API: POST /upload (file + metadata)
    API->>MinIO: Upload file
    MinIO-->>API: File path
    API->>PostgreSQL: Store metadata
    PostgreSQL-->>API: Document record
    API->>Pandoc: Convert to Markdown
    Pandoc-->>API: Markdown content
    API->>MinIO: Upload Markdown
    API-->>Client: Document with versions
```

### Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Framework** | FastAPI | 0.109.0+ |
| **Async Runtime** | uvicorn | 0.27.0+ |
| **ORM** | SQLAlchemy | 2.0.25+ |
| **Database Driver** | asyncpg | 0.29.0+ |
| **Validation** | Pydantic | 2.5.0+ |
| **Settings** | pydantic-settings | 2.1.0+ |
| **Storage** | MinIO | 7.2.0+ |
| **PDF Processing** | PyPDF2 | 3.0.0+ |
| **DOCX Processing** | python-docx | 1.1.0+ |

---

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- [pandoc](https://pandoc.org/) installed on the system
- PostgreSQL 18+ (via Docker or local install)
- MinIO (via Docker or local install)

### 1. Install Dependencies

Using uv (recommended):
```bash
uv pip install -e ".[dev]"
```

Using pip:
```bash
pip install -e .
pip install -e ".[dev]"
```

### 2. Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```bash
# Database (required)
SQLALCHEMY_DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/docmanager

# MinIO (required)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=False
MINIO_BUCKET=documents

# App (optional)
APP_SECRET_KEY=your-secret-key-here
APP_DEBUG=true
```

### 3. Start Infrastructure

Using Docker Compose (from project root):
```bash
cd ..
docker-compose up -d postgres minio
```

Or manually:
```bash
# PostgreSQL
docker run -d --name postgres -e POSTGRES_PASSWORD=password -e POSTGRES_DB=docmanager -p 5432:5432 postgres:18-alpine

# MinIO
docker run -d --name minio -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin -p 9000:9000 -p 9001:9001 minio/minio server /data --console-address ":9001"
```

### 4. Run the API

Development mode (with hot reload):
```bash
uv run uvicorn app.main:app --reload --port 8000
```

Production mode:
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000

---

## API Reference

### Endpoints

| Method | Endpoint | Description | Request Body |
|--------|----------|-------------|--------------|
| `POST` | `/upload` | Upload a new document | Multipart form with `file`, `title`, `author`, `description` |
| `GET` | `/documents/{document_id}` | Get document metadata and versions | - |
| `GET` | `/documents` | List all documents (with pagination) | Query params: `skip`, `limit` |
| `POST` | `/documents/{document_id}/validate` | Mark latest version as validated | JSON: `user_id`, `notes` |
| `GET` | `/documents/{document_id}/markdown` | Download Markdown version | - |
| `GET` | `/documents/{document_id}/download` | Download original document | - |
| `DELETE` | `/documents/{document_id}` | Delete document and all versions | - |

### Request/Response Schemas

#### Upload Document (`POST /upload`)

**Request:**
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@document.pdf" \
  -F "title=My Document" \
  -F "author=John Doe" \
  -F "description=A sample document"
```

**Response (201 Created):**
```json
{
  "id": "doc_abc123",
  "title": "My Document",
  "author": "John Doe",
  "description": "A sample document",
  "filename": "document.pdf",
  "content_type": "application/pdf",
  "created_at": "2024-01-01T00:00:00",
  "versions": [
    {
      "version": 1,
      "file_path": "documents/doc_abc123/v1/document.pdf",
      "markdown_path": "documents/doc_abc123/v1/document.md",
      "file_size": 1024,
      "status": "converted",
      "is_validated": false,
      "created_at": "2024-01-01T00:00:00"
    }
  ]
}
```

#### Get Document (`GET /documents/{document_id}`)

**Response (200 OK):**
```json
{
  "id": "doc_abc123",
  "title": "My Document",
  "author": "John Doe",
  "description": "A sample document",
  "created_at": "2024-01-01T00:00:00",
  "latest_version": 1,
  "versions": [...]
}
```

#### Validate Document (`POST /documents/{document_id}/validate`)

**Request:**
```bash
curl -X POST http://localhost:8000/documents/doc_abc123/validate \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-uuid", "notes": "Looks good"}'
```

**Response (200 OK):**
```json
{
  "message": "Document validated successfully",
  "version": 1,
  "validated_at": "2024-01-01T00:01:00",
  "validated_by": "user-uuid",
  "notes": "Looks good"
}
```

#### List Documents (`GET /documents`)

**Request:**
```bash
curl http://localhost:8000/documents?skip=0&limit=10
```

**Response (200 OK):**
```json
{
  "documents": [...],
  "total": 100,
  "skip": 0,
  "limit": 10
}
```

---

## Project Structure

### Module Dependencies

```mermaid
flowchart TB
    main[main.py\nFastAPI App] --> config[config.py\nSettings]
    main --> models[models.py\nPydantic Schemas]
    main --> crud[crud.py\nDatabase Ops]
    main --> storage[storage.py\nMinIO Client]
    main --> processors[processors.py\nConversion]
    
    crud --> database[database.py\nSQLAlchemy]
    storage --> database
    processors --> storage
    
    tests[tests/] --> main
    tests --> conftest[conftest.py\nFixtures]
```

### Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py           # Application settings (pydantic-settings)
│   ├── database.py         # SQLAlchemy async engine, session, and models
│   │                          # - Centralized DbSession dependency
│   │                          # - init_db() for table creation
│   ├── models.py           # Pydantic request/response schemas
│   ├── auth.py             # JWT authentication middleware
│   │                          # - Token creation/decoding
│   │                          # - Current user dependencies
│   ├── exceptions.py       # Custom exception hierarchy
│   │                          # - DryDocsError base class
│   │                          # - Document, Storage, Processing, Search, Reference errors
│   ├── processors.py       # Document processing (PDF/DOCX to MD)
│   │                          # - Text extraction from PDF/DOCX
│   │                          # - Markdown conversion via Pandoc
│   │                          # - Reference extraction from text
│   ├── storage.py          # MinIO client and file storage operations
│   │                          # - Async file upload/download/delete
│   │                          # - Presigned URL generation
│   ├── transactions.py     # DB transaction utilities
│   │                          # - Transaction context managers
│   │                          # - Retry logic with exponential backoff
│   │                          # - Batch processing utilities
│   ├── crud/               # Data access layer (separated by domain)
│   │   ├── __init__.py
│   │   ├── documents.py    # Document CRUD operations
│   │   ├── versions.py     # Version CRUD operations
│   │   ├── references.py   # Reference CRUD & extraction
│   │   └── search.py       # Full-text search operations
│   └── routes/             # API endpoints (FastAPI routers)
│       ├── __init__.py
│       ├── documents.py   # /documents/* endpoints
│       │                    # - POST /upload
│       │                    # - GET /documents
│       │                    # - GET /documents/{id}
│       │                    # - DELETE /documents/{id}
│       │                    # - POST /documents/{id}/validate
│       │                    # - GET /documents/{id}/markdown
│       │                    # - GET /documents/{id}/download
│       ├── references.py   # /references/* endpoints
│       │                    # - GET /documents/{id}/references
│       │                    # - POST /documents/{id}/extract-references
│       │                    # - GET /documents/{id}/references/outgoing
│       │                    # - GET /documents/{id}/references/incoming
│       └── search.py       # /search endpoints
│            # - POST /search
│            # - GET /documents/{id}/search
│
├── alembic/               # Database migration scripts
│   ├── env.py              # Alembic environment configuration
│   ├── script.py.mako      # Migration script template
│   └── versions/          # Migration history
│       └── ...             # Individual migration files
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Pytest fixtures with mocks
│   ├── test_crud.py        # CRUD operation tests
│   ├── test_exceptions.py  # Exception hierarchy tests
│   └── test_routes.py      # API endpoint tests
│
├── pyproject.toml          # Project metadata and dependencies
├── Dockerfile              # Container configuration
├── .env.example            # Environment variables template
├── .env.dev                # Development environment variables
├── .gitignore
└── README.md
```

### Architecture Layers

```mermaid
flowchart TB
    subgraph "API Layer"
        routes[routes/
        documents.py
        references.py
        search.py]
    end
    
    subgraph "Service Layer"
        crud[crud/
        documents.py
        versions.py
        references.py
        search.py]
        processors[processors.py
        Text extraction
        MD conversion
        Reference parsing]
        auth[auth.py
        JWT middleware]
        transactions[transactions.py
        DB transactions
        Retry logic]
    end
    
    subgraph "Data Layer"
        database[database.py
        SQLAlchemy Models
        DbSession dependency]
        storage[storage.py
        MinIO Client]
    end
    
    subgraph "External Services"
        postgres[PostgreSQL
        Metadata DB]
        minio[MinIO
        Object Storage]
    end
    
    %% Dependencies
    config[config.py
        Settings]
    config --> database
    config --> storage
    config --> auth
    
    database --> postgres
    storage --> minio
    
    routes --> crud
    routes --> storage
    routes --> auth
    routes --> config
    
    crud --> database
    crud --> transactions
    processors --> storage
    auth --> config
    transactions --> database
```

---

## Configuration

### Settings (app/config.py)

All application settings are managed via `pydantic-settings` with type validation:

```python
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # PostgreSQL Configuration
    postgres_host: str = Field(default="localhost", min_length=1)
    postgres_port: int = Field(default=5432, ge=1, le=65535)
    postgres_user: str = Field(default="postgres", min_length=1)
    postgres_password: str = Field(default="password", min_length=1)
    postgres_db: str = Field(default="docmanager", min_length=1)
    
    # MinIO Configuration
    minio_endpoint: str = Field(default="localhost:9000", min_length=1)
    minio_access_key: str = Field(default="minioadmin", min_length=1)
    minio_secret_key: str = Field(default="minioadmin", min_length=1)
    minio_bucket: str = Field(default="documents", min_length=1)
    minio_secure: bool = False
    
    # Authentication (JWT)
    better_auth_secret: str = Field(default="...", min_length=16)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
```

**Configuration Sources** (in priority order):
1. Environment variables
2. `.env` file in the backend directory
3. Default values defined in the `Settings` class

**Derived Properties:**
- `postgres_url`: Auto-generated async PostgreSQL connection URL

> **Note**: The `better_auth_secret` must match the secret configured in the frontend's `better-auth` setup.

---

## Development Commands

| Command | Description |
|---------|-------------|
| `uv pip install -e ".[dev]"` | Install all dependencies (including dev) |
| `uv run uvicorn app.main:app --reload` | Run development server |
| `ruff check app/` | Run linter (PEP 8 compliance) |
| `ruff check app/ --fix` | Auto-fix linting issues |
| `ruff format app/` | Format code |
| `ty check` | Run type checker |
| `pytest` | Run all tests |
| `pytest --cov=app --cov-report=html` | Run tests with coverage |
| `alembic revision --autogenerate -m "description"` | Create new migration |
| `alembic upgrade head` | Apply all pending migrations |
| `alembic downgrade -1` | Rollback last migration |

### Testing

The test suite uses `pytest` with `pytest-asyncio` for async test support. All database and storage operations are **mocked** in tests, so no external services are required.

**Test Files:**
- `tests/test_crud.py` - Tests for CRUD operations (create, read, update, delete)
- `tests/test_exceptions.py` - Tests for custom exception hierarchy
- `tests/test_routes.py` - Tests for API endpoints

**Run tests:**
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_crud.py

# Run specific test
pytest tests/test_crud.py::test_create_document -v

# Run with verbose output
pytest -v

# Run only failed tests from last run
pytest --lf
```

> **Note**: Tests use comprehensive mocking (via `unittest.mock`) to avoid requiring real database or MinIO instances. See `tests/conftest.py` for fixture setup.

---

## Database Migrations

The project uses **Alembic** for database schema migrations.

### Migration Workflow

1. **Create a new migration** (after changing models in `database.py`):
   ```bash
   alembic revision --autogenerate -m "add_search_vector_to_documents"
   ```

2. **Review the generated migration** in `alembic/versions/`

3. **Apply migrations** to your database:
   ```bash
   alembic upgrade head
   ```

4. **Rollback** if needed:
   ```bash
   alembic downgrade -1  # Rollback one migration
   alembic downgrade base  # Rollback all migrations
   ```

### Migration Files

Migrations are stored in `alembic/versions/` with filenames like `1234abc_add_column.py`. Each file contains:
- `upgrade()`: Applies the schema changes
- `downgrade()`: Reverts the schema changes

### Alembic Configuration

The `alembic/env.py` is configured to work with the async SQLAlchemy setup. The `target_metadata` is set to `Base.metadata` from `app.database`.

**Common Alembic Commands:**
```bash
alembic current              # Show current revision
alembic history              # Show migration history
alembic show head             # Show SQL for current head
alembic merge heads           # Merge multiple heads
```

---

## Docker

### Build Image

```bash
docker build -t drydocs-backend .
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (including pandoc)
RUN apt-get update && apt-get install -y pandoc && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

# Copy application code
COPY app/ ./app/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Run with Docker

```bash
docker run -d \
  --name drydocs-backend \
  -p 8000:8000 \
  -e postgres_host=host.docker.internal \
  -e postgres_port=5432 \
  -e postgres_user=postgres \
  -e postgres_password=password \
  -e postgres_db=docmanager \
  -e minio_endpoint=host.docker.internal:9000 \
  -e minio_access_key=minioadmin \
  -e minio_secret_key=minioadmin \
  -e better_auth_secret=your-strong-secret-here \
  drydocs-backend
```

**Docker Compose Alternative:**

For full-stack deployment, add the backend service to your `docker-compose.yaml`:

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - minio
    environment:
      - postgres_host=postgres
      - postgres_port=5432
      - postgres_user=postgres
      - postgres_password=password
      - postgres_db=docmanager
      - minio_endpoint=minio:9000
      - minio_access_key=minioadmin
      - minio_secret_key=minioadmin
      - better_auth_secret=your-strong-secret-here
```

Then run: `docker-compose up -d backend`

---

## Dependencies

### Core Dependencies

| Package | Purpose | Version |
|---------|---------|---------|
| `fastapi[standard]` | Web framework | 0.109.0+ |
| `uvicorn[standard]` | ASGI server | 0.27.0+ |
| `sqlalchemy[asyncio]` | ORM | 2.0.25+ |
| `asyncpg` | PostgreSQL async driver | 0.29.0+ |
| `pydantic` | Data validation | 2.5.0+ |
| `pydantic-settings` | Settings management | 2.1.0+ |
| `python-multipart` | Multipart form handling | 0.0.6+ |
| `minio` | S3-compatible storage | 7.2.0+ |
| `pypdf` | PDF text extraction | 4.0.0+ |
| `python-docx` | DOCX text extraction | 1.1.0+ |
| `python-jose[cryptography]` | JWT handling | 3.3.0+ |

### Development Dependencies

| Package | Purpose | Version |
|---------|---------|---------|
| `pytest` | Test framework | 9.0.3+ |
| `pytest-asyncio` | Async test support | 0.23.0+ |
| `httpx` | HTTP client for tests | 0.26.0+ |
| `pytest-cov` | Coverage reporting | 4.1.0+ |
| `ruff` | Linter & formatter | 0.1.0+ |
| `ty` | Type checker | 0.0.34+ |
| `alembic` | Database migrations | 1.13.0+ |

---

## Environment Variables

### PostgreSQL

| Variable | Description | Default |
|----------|-------------|---------|
| `postgres_host` | Database hostname | `localhost` |
| `postgres_port` | Database port | `5432` |
| `postgres_user` | Database username | `postgres` |
| `postgres_password` | Database password | `password` |
| `postgres_db` | Database name | `docmanager` |

### MinIO

| Variable | Description | Default |
|----------|-------------|---------|
| `minio_endpoint` | MinIO server endpoint | `localhost:9000` |
| `minio_access_key` | MinIO access key | `minioadmin` |
| `minio_secret_key` | MinIO secret key | `minioadmin` |
| `minio_bucket` | Default bucket name | `documents` |
| `minio_secure` | Use HTTPS | `False` |

### Authentication

| Variable | Description | Default |
|----------|-------------|---------|
| `better_auth_secret` | JWT signing secret | (32+ chars recommended) |
| `jwt_algorithm` | JWT algorithm | `HS256` |
| `access_token_expire_minutes` | Token expiration | `30` |

### CORS

| Variable | Description | Default |
|----------|-------------|---------|
| `cors_origins` | Allowed origins (comma-separated) | `http://localhost:3000,http://localhost:5173` |

---

## Troubleshooting

### Pandoc Not Found

Ensure pandoc is installed on your system:

- **Ubuntu/Debian**: `sudo apt-get install pandoc`
- **macOS**: `brew install pandoc`
- **Windows**: Download from [pandoc.org](https://pandoc.org/installing.html)

Verify installation:
```bash
pandoc --version
```

### Database Connection Issues

1. Verify PostgreSQL is running:
   ```bash
   docker ps | grep postgres
   ```

2. Test connection:
   ```bash
   psql postgresql://postgres:password@localhost:5432/docmanager
   ```

3. Check database tables are created (happens automatically on startup)

### MinIO Connection Issues

1. Verify MinIO is running:
   ```bash
   docker ps | grep minio
   ```

2. Access MinIO console at http://localhost:9001
3. Verify bucket `documents` exists (created automatically on first upload)

### CORS Issues

If accessing from a different origin, ensure CORS is configured in `app/main.py`. The backend should have:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
