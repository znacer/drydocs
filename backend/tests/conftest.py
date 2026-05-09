"""Pytest fixtures for the DryDocs backend."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


# Mock environment variables for testing
@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
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


# HTTP client for API tests
@pytest.fixture
def client():
    """Create HTTP client for testing FastAPI endpoints."""
    # Mock the database and storage dependencies
    with patch("app.routes.documents.get_db_session") as mock_db, \
         patch("app.routes.search.get_db_session") as mock_search_db, \
         patch("app.routes.references.get_db_session") as mock_ref_db, \
         patch("app.main.init_db") as mock_init, \
         patch("app.main.ensure_bucket") as mock_bucket:

        # Create mock async session
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        mock_db.return_value = mock_session
        mock_search_db.return_value = mock_session
        mock_ref_db.return_value = mock_session
        mock_init.return_value = None
        mock_bucket.return_value = None

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
