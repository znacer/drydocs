# Document Manager API - Phase 1

A FastAPI-based documentation manager with PostgreSQL, MinIO, and Markdown conversion.

## Features

- **Document Upload**: Upload PDF and Word documents
- **Versioning**: Automatic version tracking for each document
- **Markdown Conversion**: Convert documents to Markdown using pandoc
- **Validation**: Mark document versions as validated
- **Storage**: Files stored in MinIO, metadata in PostgreSQL

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- [pandoc](https://pandoc.org/) installed on the system
- Docker and Docker Compose (for local development)

## Quick Start

### 1. Install Dependencies

Using uv:
```bash
cd backend
uv pip install -r pyproject.toml
```

Using pip:
```bash
cd backend
pip install -e .
```

### 2. Set Up Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your configuration, or use the defaults for local development.

### 3. Start Services with Docker Compose

```bash
cd backend
docker-compose up -d
```

This starts:
- PostgreSQL on port 5432
- MinIO on port 9000 (console on 9001)
- API on port 8000

### 4. Initialize Database

The database tables are created automatically on first startup.

### 5. Run the API

```bash
cd backend
uv pip install uvicorn
uv run uvicorn app.main:app --reload --port 8000
```

Or with the installed package:
```bash
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload a document (PDF/Word) with metadata |
| GET | `/documents/{document_id}` | Get document metadata and latest version |
| POST | `/documents/{document_id}/validate` | Mark latest version as validated |
| GET | `/documents/{document_id}/markdown` | Download Markdown version |

### Upload Request

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@document.pdf" \
  -F "title=My Document" \
  -F "author=John Doe" \
  -F "description=Sample document"
```

### Get Document

```bash
curl http://localhost:8000/documents/{document_id}
```

### Validate Document

```bash
curl -X POST http://localhost:8000/documents/{document_id}/validate \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-uuid", "notes": "Looks good"}'
```

### Download Markdown

```bash
curl http://localhost:8000/documents/{document_id}/markdown \
  -o document.md
```

## Docker Build

To build the API Docker image:

```bash
docker build -t drydocs-api .
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py        # Settings with pydantic-settings
│   ├── database.py      # SQLAlchemy async setup
│   ├── models.py        # Pydantic schemas
│   ├── storage.py       # MinIO client
│   ├── processors.py    # Document processing
│   ├── crud.py          # Database operations
│   └── main.py          # FastAPI app and routes
├── pyproject.toml       # Dependencies
├── .env.example         # Environment template
├── docker-compose.yml   # Local dev services
└── README.md
```

## Dependencies

- **FastAPI**: Web framework
- **SQLAlchemy**: Async ORM with asyncpg for PostgreSQL
- **Pydantic**: Data validation and schemas
- **MinIO**: S3-compatible object storage
- **PyPDF2**: PDF text extraction
- **python-docx**: Word document text extraction
- **pandoc**: Document to Markdown conversion (system dependency)

## Notes

- Ensure pandoc is installed on your system. On Ubuntu: `sudo apt-get install pandoc`
- On macOS: `brew install pandoc`
- MinIO credentials: Access the console at http://localhost:9001 with username `minioadmin` and password `minioadmin`
