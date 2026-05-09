"""Pytest fixtures for the DryDocs backend.

This module provides fixtures for testing the DryDocs backend API.
It uses comprehensive mocking to avoid requiring a real database or MinIO instance.
"""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

# =============================================================================
# Mock Setup - patch before importing app
# =============================================================================
# First, import the modules we need to patch
import app.database as db_module
import app.storage as storage_module
from app.main import app

# Save originals
_original_init_db = db_module.init_db
_original_async_session_local = db_module.AsyncSessionLocal
_original_minio_client = storage_module.minio_client


# Create a mock result object that behaves like SQLAlchemy Result
class MockResult:
    """Mock SQLAlchemy Result object."""

    def __init__(self, scalar_value=None, scalars_list=None, rows=None):
        self._scalar_value = scalar_value
        self._scalars_list = scalars_list or []
        self._rows = rows or []

    def scalar_one_or_none(self):
        return self._scalar_value

    def scalar_one(self):
        return self._scalar_value if self._scalar_value is not None else 0

    def scalars(self):
        return MockScalars(self._scalars_list)

    def all(self):
        return self._rows if self._rows else self._scalars_list

    def first(self):
        return (
            self._rows[0] if self._rows else (self._scalars_list[0] if self._scalars_list else None)
        )

    def __iter__(self):
        """Make MockResult iterable for search queries."""
        return iter(self._rows)


class MockScalars:
    """Mock SQLAlchemy scalars result."""

    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


# Create mock async session generator
@asynccontextmanager
async def _mock_async_session_local() -> AsyncGenerator[AsyncSession, None]:
    """Mock AsyncSessionLocal that returns a mock session."""
    mock_session = MagicMock(spec=AsyncSession)

    # Make execute an async function that returns MockResult
    async def mock_execute(stmt, *args, **kwargs):
        stmt_str = str(stmt)
        if "count" in stmt_str.lower():
            return MockResult(scalar_value=0)
        elif "documents" in stmt_str.lower():
            return MockResult(scalar_value=None, scalars_list=[])
        else:
            return MockResult(scalar_value=None, scalars_list=[])

    mock_session.execute = mock_execute
    mock_session.add = AsyncMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.expire_on_commit = False

    try:
        yield mock_session
    finally:
        pass


# Create mock MinIO client
class _MockMinIOClient:
    """Mock MinIO client that works with async/await."""

    async def ensure_bucket(self) -> None:
        pass

    async def upload_file(self, bucket: str, object_name: str, file_data: bytes):
        return MagicMock()

    async def download_file(self, bucket: str, object_name: str) -> bytes:
        return b""

    async def file_exists(self, bucket: str, object_name: str) -> bool:
        return False

    async def delete_file(self, bucket: str, object_name: str) -> bool:
        return True

    async def delete_files_by_prefix(self, bucket: str, prefix: str) -> int:
        return 0

    async def list_files(self, bucket: str, prefix: str | None = None) -> list[str]:
        return []

    async def get_presigned_url(self, bucket: str, object_name: str, expiry: int = 3600) -> str:
        return "http://mock.url"


# Apply patches at module level (before app import)
db_module.init_db = AsyncMock()  # type : ignore
storage_module.ensure_bucket = AsyncMock()  # type: ignore
db_module.AsyncSessionLocal = _mock_async_session_local  # type: ignore
storage_module.minio_client = _MockMinIOClient()  # type: ignore


# =============================================================================
# Fixtures
# =============================================================================


# Mock environment variables for testing
@pytest.fixture(scope="session", autouse=True)
def setup_test_env() -> None:
    """Setup test environment variables."""
    os.environ["postgres_host"] = "localhost"
    os.environ["postgres_port"] = "5432"
    os.environ["postgres_user"] = "postgres"
    os.environ["postgres_password"] = "password"
    os.environ["postgres_db"] = "docmanager"
    os.environ["minio_endpoint"] = "localhost:9000"
    os.environ["minio_access_key"] = "minioadmin"
    os.environ["minio_secret_key"] = "minioadmin"
    os.environ["minio_bucket"] = "documents"
    os.environ["better_auth_secret"] = "test-secret-key-for-testing-only"


# HTTP client for API tests
@pytest.fixture
def client():
    """Create HTTP client for testing FastAPI endpoints.

    All database and storage operations are mocked at the module level.
    """
    with TestClient(app) as client:
        yield client


# Sample document data for tests
@pytest.fixture
def sample_document_data():
    """Sample document data for testing."""
    return {
        "title": "Test Document",
        "author": "Test Author",
        "description": "A test document for testing purposes",
    }


@pytest.fixture
def sample_version_data():
    """Sample version data for testing."""
    return {
        "filename": "test.pdf",
        "file_type": "PDF",
        "file_size": 1024,
        "storage_path": "test/1/test.pdf",
        "markdown_path": "test/1/document.md",
        "extracted_text": "This is test content",
    }


# =============================================================================
# Restore originals after tests
# =============================================================================


@pytest.fixture(scope="session", autouse=True)
def restore_originals():
    """Restore original module state after all tests complete."""
    yield
    # Restore originals
    db_module.init_db = _original_init_db
    db_module.AsyncSessionLocal = _original_async_session_local
    storage_module.minio_client = _original_minio_client
