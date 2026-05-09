"""Tests for CRUD operations."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.crud import (
    create_document,
    delete_document,
    list_documents,
)
from app.models import DocumentCreate, DocumentListResponse


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    mock_session = MagicMock()
    mock_session.execute = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    return mock_session


@pytest.mark.asyncio
async def test_create_document(mock_db_session, sample_document_data):
    """Test creating a new document."""
    from app.database import Document

    doc_create = DocumentCreate(**sample_document_data)

    # Mock the document model
    mock_doc = MagicMock(spec=Document)
    mock_doc.id = str(uuid4())
    mock_doc.title = sample_document_data["title"]
    mock_doc.author = sample_document_data["author"]
    mock_doc.description = sample_document_data["description"]
    mock_doc.current_version = 1
    mock_doc.status = "draft"

    # Mock the result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    with patch("app.crud.documents.uuid.uuid4", return_value=uuid4()):
        with patch("app.crud.documents.Document", return_value=mock_doc):
            result = await create_document(mock_db_session, doc_create)

    assert result.id is not None
    assert result.title == sample_document_data["title"]
    assert result.author == sample_document_data["author"]
    assert result.status == "draft"


@pytest.mark.asyncio
async def test_list_documents_empty(mock_db_session):
    """Test listing documents when none exist."""
    mock_result = MagicMock()
    mock_result.scalar_one = MagicMock(return_value=0)
    mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    result = await list_documents(mock_db_session, skip=0, limit=10)

    assert isinstance(result, DocumentListResponse)
    assert result.count == 0


@pytest.mark.asyncio
async def test_delete_document_not_found(mock_db_session):
    """Test deleting a non-existent document."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    result = await delete_document(mock_db_session, str(uuid4()), cleanup_storage=False)
    assert result is False
