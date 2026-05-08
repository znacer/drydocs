# DryDocs Backend

> **FastAPI-based Document Management API**
>
> Secure document upload, storage, versioning, and Markdown conversion service.

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
│   ├── models.py           # Pydantic request/response schemas
│   ├── crud.py             # Database CRUD operations
│   ├── storage.py          # MinIO client and file storage operations
│   ├── processors.py       # Document conversion logic (PDF/DOCX to MD)
│   └── main.py             # FastAPI app, routes, and dependencies
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Pytest fixtures
│   ├── test_upload.py      # Upload endpoint tests
│   ├── test_documents.py   # Document retrieval tests
│   └── test_validation.py  # Validation endpoint tests
│
├── pyproject.toml          # Project metadata and dependencies
├── Dockerfile              # Container configuration
├── .env.example            # Environment variables template
├── .env.dev                # Development environment variables
├── .gitignore
└── README.md
```

---

## Configuration

### Settings (app/config.py)

All application settings are managed via `pydantic-settings`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    sqlalchemy_database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/docmanager"
    
    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket: str = "documents"
    
    # App
    app_secret_key: str = "secret"
    app_debug: bool = False
```

Settings are automatically loaded from:
1. Environment variables (prefixed with uppercase class name)
2. `.env` file in the project directory
3. Default values defined in the class

---

## Development Commands

| Command | Description |
|---------|-------------|
| `uv pip install -e ".[dev]"` | Install all dependencies (including dev) |
| `uv run uvicorn app.main:app --reload` | Run development server |
| `ruff check app/` | Run linter (PEP 8 compliance) |
| `ruff format app/` | Format code |
| `mypy app/` | Run type checker |
| `pytest` | Run all tests |
| `pytest --cov=app` | Run tests with coverage |
| `pytest tests/test_upload.py` | Run specific test file |

### Testing

The test suite uses `pytest` with `pytest-asyncio` for async test support.

**Prerequisites for testing:**
- Test database (configured via `TEST_SQLALCHEMY_DATABASE_URL`)
- Test MinIO instance (configured via `TEST_MINIO_*` variables)

**Run tests:**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_upload.py::test_upload_pdf
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
  -e SQLALCHEMY_DATABASE_URL=postgresql+asyncpg://postgres:password@host.docker.internal:5432/docmanager \
  -e MINIO_ENDPOINT=host.docker.internal:9000 \
  drydocs-backend
```

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
| `PyPDF2` | PDF text extraction | 3.0.0+ |
| `python-docx` | DOCX text extraction | 1.1.0+ |

### Development Dependencies

| Package | Purpose | Version |
|---------|---------|---------|
| `pytest` | Test framework | 9.0.3+ |
| `pytest-asyncio` | Async test support | 0.23.0+ |
| `httpx` | HTTP client for tests | 0.26.0+ |
| `pytest-cov` | Coverage reporting | 4.1.0+ |
| `ruff` | Linter & formatter | 0.1.0+ |
| `mypy` | Type checker | 1.8.0+ |

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SQLALCHEMY_DATABASE_URL` | PostgreSQL connection URL | `postgresql+asyncpg://postgres:password@localhost:5432/docmanager` |
| `MINIO_ENDPOINT` | MinIO server endpoint | `localhost:9000` |
| `MINIO_ACCESS_KEY` | MinIO access key | `minioadmin` |
| `MINIO_SECRET_KEY` | MinIO secret key | `minioadmin` |
| `MINIO_SECURE` | Use HTTPS for MinIO | `False` |
| `MINIO_BUCKET` | MinIO bucket name | `documents` |
| `APP_SECRET_KEY` | Application secret key | `secret` |
| `APP_DEBUG` | Enable debug mode | `False` |

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
