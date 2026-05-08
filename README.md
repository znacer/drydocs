# DryDocs

> **Document Management System**
>
> Securely upload, store, version, and convert PDF and Word documents to Markdown.

---

## Overview

DryDocs is a full-stack document management system that handles the complete lifecycle of documents — from upload and secure storage to automated Markdown conversion and validation workflows.

### Key Features

- **Document Upload**: Upload PDF and DOCX files with metadata (title, author, description)
- **Version Tracking**: Automatic version history for every document update
- **Markdown Conversion**: Automated conversion of documents to Markdown format using Pandoc
- **Validation Workflows**: Mark versions as validated with user notes
- **Secure Storage**: Files stored in MinIO (S3-compatible), metadata in PostgreSQL
- **Internationalization**: Multi-language support via Paraglide-js
- **Authentication**: Email/password auth with better-auth

### Architecture

```mermaid
flowchart TB
    subgraph DryDocs
        Frontend[SvelteKit\nFrontend]
        Backend[FastAPI\nBackend]
        Storage[MinIO\nStorage]
        Database[PostgreSQL\nMetadata]
    end
    
    Frontend -->|HTTP requests| Backend
    Backend -->|Store files| Storage
    Backend -->|Store metadata| Database
    Storage -->|S3 API| Backend
    Database -->|SQL| Backend
```

### Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Svelte 5 (Runes), TypeScript, Tailwind CSS v4, daisyUI |
| **Backend** | FastAPI, Python 3.11+, SQLAlchemy 2.0 (Async) |
| **Database** | PostgreSQL 18, Drizzle ORM |
| **Storage** | MinIO (S3-compatible object storage) |
| **Auth** | better-auth (Email/Password) |
| **Conversion** | Pandoc, PyPDF2, python-docx |
| **Validation** | Pydantic v2 |
| **i18n** | Paraglide-js |

---

## Getting Started

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| [Docker](https://www.docker.com/) | Latest | PostgreSQL & MinIO services |
| [Docker Compose](https://docs.docker.com/compose/) | Latest | Service orchestration |
| [Python](https://www.python.org/) | 3.11+ | Backend runtime |
| [uv](https://github.com/astral-sh/uv) | Latest | Python dependency management (recommended) |
| [Node.js](https://nodejs.org/) | 20+ | Frontend runtime |
| [Bun](https://bun.sh/) | Latest | Frontend package management |
| [Pandoc](https://pandoc.org/) | Latest | Document conversion |

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd drydocs
   ```

2. **Start infrastructure services**
   ```bash
   docker-compose up -d postgres minio
   ```
   This starts:
   - PostgreSQL on `localhost:5432` (Database: `docmanager`, User: `postgres`, Password: `password`)
   - MinIO on `localhost:9000` (Console: `localhost:9001`, User: `minioadmin`, Password: `minioadmin`)

3. **Set up backend**
   ```bash
   cd backend
   uv pip install -e ".[dev]"
   uv run uvicorn app.main:app --reload --port 8000
   ```

4. **Set up frontend** (in a new terminal)
   ```bash
   cd frontend
   bun install
   bun run dev --port 3000
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - MinIO Console: http://localhost:9001

---

## Project Structure

```
drydocs/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── config.py           # Application configuration (pydantic-settings)
│   │   ├── database.py         # SQLAlchemy async models & session
│   │   ├── models.py           # Pydantic schemas
│   │   ├── crud.py             # Database CRUD operations
│   │   ├── storage.py          # MinIO client & file operations
│   │   ├── processors.py       # Document conversion logic
│   │   └── main.py             # FastAPI routes & app entry
│   ├── pyproject.toml          # Python dependencies
│   ├── Dockerfile
│   └── README.md
│
├── frontend/                   # SvelteKit Frontend
│   ├── src/
│   │   ├── lib/
│   │   │   ├── components/     # Reusable UI components
│   │   │   ├── server/         # Server-only logic (Auth, DB)
│   │   │   └── utils/          # API client & utilities
│   │   └── routes/             # Pages & API endpoints
│   ├── package.json
│   ├── svelte.config.js
│   └── README.md
│
├── docker-compose.yaml         # Infrastructure services
├── AGENTS.md                   # AI agent guidelines
└── README.md                   # This file
```

---

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload` | Upload a document (PDF/DOCX) with metadata |
| `GET` | `/documents/{id}` | Get document metadata and versions |
| `POST` | `/documents/{id}/validate` | Mark latest version as validated |
| `GET` | `/documents/{id}/markdown` | Download Markdown version |
| `GET` | `/documents/{id}/download` | Download original document |

### Upload Example

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@document.pdf" \
  -F "title=My Document" \
  -F "author=John Doe" \
  -F "description=A sample PDF document"
```

### Response Example

```json
{
  "id": "doc_abc123",
  "title": "My Document",
  "author": "John Doe",
  "description": "A sample PDF document",
  "filename": "document.pdf",
  "content_type": "application/pdf",
  "versions": [
    {
      "version": 1,
      "created_at": "2024-01-01T00:00:00",
      "file_size": 1024,
      "status": "converted",
      "is_validated": false
    }
  ]
}
```

---

## Development

### Backend Commands

| Command | Description |
|---------|-------------|
| `uv pip install -e ".[dev]"` | Install dependencies |
| `uv run uvicorn app.main:app --reload` | Run dev server |
| `ruff check app/` | Lint code |
| `mypy app/` | Type check |
| `pytest` | Run tests |

### Frontend Commands

| Command | Description |
|---------|-------------|
| `bun install` | Install dependencies |
| `bun run dev` | Run dev server |
| `bun run build` | Build for production |
| `bun run lint` | Lint code |
| `bun run check` | Type check |
| `bun run db:push` | Push database schema |
| `bun run auth:schema` | Generate auth schema |

### Environment Variables

#### Backend (`.env` in `/backend`)

```bash
# Database
SQLALCHEMY_DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/docmanager

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=False
MINIO_BUCKET=documents

# App
APP_SECRET_KEY=your-secret-key-here
```

#### Frontend (`.env` in `/frontend`)

```bash
# Backend API
VITE_API_URL=http://localhost:8000

# Database (for Drizzle)
DATABASE_URL=postgresql://postgres:password@localhost:5432/docmanager

# Auth
AUTH_SECRET=your-auth-secret-here
AUTH_URL=http://localhost:3000
```

---

## Docker

### Build Images

```bash
# Backend
docker build -t drydocs-backend ./backend

# Frontend
docker build -t drydocs-frontend ./frontend
```

### Run with Docker Compose

Uncomment the backend and frontend services in `docker-compose.yaml` for full-stack deployment:

```yaml
services:
  # ... existing postgres & minio ...
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - minio
    environment:
      - SQLALCHEMY_DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/docmanager
      - MINIO_ENDPOINT=minio:9000

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

Then run:
```bash
docker-compose up -d
```

---

## Conventions

### Backend (Python)

- **Style**: PEP 8 compliant, enforced by Ruff
- **Types**: Mandatory type hints, checked with mypy
- **Async**: Use `async/await` for all I/O operations
- **Schemas**: Pydantic v2 models in `app/models.py`

### Frontend (Svelte/TypeScript)

- **Runes**: Use Svelte 5 runes (`$state`, `$props`, `$derived`)
- **Types**: Strict TypeScript for all components
- **Components**: Focused, reusable components in `src/lib/components`
- **API**: Centralized client in `src/lib/utils/api.ts`

---

## Infrastructure Notes

- **PostgreSQL**: Port 5432, Database `docmanager`
- **MinIO**: API Port 9000, Console Port 9001, Bucket `documents`
- **Pandoc**: Must be installed on the system for document conversion
  - Ubuntu: `sudo apt-get install pandoc`
  - macOS: `brew install pandoc`
  - Windows: Download from [pandoc.org](https://pandoc.org/installing.html)
