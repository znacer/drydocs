"""Document CRUD operations."""

import logging
import uuid

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import Document, DocumentReference, Version
from app.models import (
    DocumentCreate,
    DocumentListResponse,
    DocumentResponse,
    DocumentWithLatestVersion,
    VersionResponse,
)
from app.storage import delete_files_by_prefix, list_files

logger = logging.getLogger(__name__)


async def create_document(db: AsyncSession, document_data: DocumentCreate) -> DocumentResponse:
    """
    Create a new document in the database.

    Args:
        db: Async database session
        document_data: Document data to create

    Returns:
        Created document as DocumentResponse
    """
    try:
        doc_id = str(uuid.uuid4())
        db_document = Document(
            id=doc_id,
            title=document_data.title,
            author=document_data.author,
            description=document_data.description,
            current_version=1,
            status="draft",
        )
        db.add(db_document)
        await db.flush()
        await db.refresh(db_document)

        logger.debug(f"Created document: {doc_id}")
        return DocumentResponse.model_validate(db_document)
    except Exception as e:
        logger.error(f"Error creating document: {e}")
        raise


async def get_document(db: AsyncSession, document_id: str) -> DocumentWithLatestVersion | None:
    """
    Get a document with its latest version.

    Args:
        db: Async database session
        document_id: Document ID

    Returns:
        DocumentWithLatestVersion or None if not found
    """
    try:
        result = await db.execute(
            select(Document)
            .where(Document.id == document_id)
            .options(selectinload(Document.versions))
        )
        db_document = result.scalar_one_or_none()

        if db_document is None:
            logger.debug(f"Document not found: {document_id}")
            return None

        latest_version = None
        if db_document.versions:
            latest_version = db_document.versions[0]

        return DocumentWithLatestVersion(
            document=DocumentResponse.model_validate(db_document),
            latest_version=VersionResponse.model_validate(latest_version)
            if latest_version
            else None,
        )
    except Exception as e:
        logger.error(f"Error fetching document: {e}")
        raise


async def list_documents(db: AsyncSession, skip: int = 0, limit: int = 100) -> DocumentListResponse:
    """
    List all documents with pagination.

    Args:
        db: Async database session
        skip: Number of documents to skip (offset)
        limit: Maximum number of documents to return

    Returns:
        DocumentListResponse with list of documents and count
    """
    try:
        # Get count
        count_result = await db.execute(select(func.count()).select_from(Document))
        total_count = count_result.scalar_one()

        # Get documents
        result = await db.execute(
            select(Document).offset(skip).limit(limit).order_by(Document.created_at.desc())
        )
        db_documents = result.scalars().all()

        documents = [DocumentResponse.model_validate(doc) for doc in db_documents]

        return DocumentListResponse(documents=documents, count=total_count)
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise


async def delete_document(
    db: AsyncSession,
    document_id: str,
    cleanup_storage: bool = True,
) -> bool:
    """Delete a document and all its associated data (versions, references, storage files).

    Args:
        db: Async database session
        document_id: Document ID to delete
        cleanup_storage: Whether to also delete files from MinIO storage

    Returns:
        True if document was deleted, False if not found
    """
    from app.config import settings

    try:
        # Find the document
        result = await db.execute(select(Document).where(Document.id == document_id))
        db_document = result.scalar_one_or_none()

        if db_document is None:
            logger.warning(f"Document not found for deletion: {document_id}")
            return False

        # Get document prefix for storage cleanup (e.g., "doc-id/")
        doc_prefix = f"{document_id}/"

        # Delete all references where this document is the source
        await db.execute(
            delete(DocumentReference).where(DocumentReference.source_document_id == document_id)
        )

        # Delete all references where this document is the target
        await db.execute(
            delete(DocumentReference).where(DocumentReference.referenced_document_id == document_id)
        )

        # Delete all versions of the document
        await db.execute(delete(Version).where(Version.document_id == document_id))

        # Delete the document
        await db.execute(delete(Document).where(Document.id == document_id))

        # Clean up storage files if requested
        if cleanup_storage:
            try:
                files_to_delete = await list_files(settings.minio_bucket, doc_prefix)
                if files_to_delete:
                    deleted_count = await delete_files_by_prefix(settings.minio_bucket, doc_prefix)
                    logger.info(f"Deleted {deleted_count} storage files for document {document_id}")
            except Exception as e:
                # Log but don't fail the document deletion
                logger.warning(f"Failed to clean up storage for document {document_id}: {e}")

        logger.info(f"Deleted document: {document_id}")
        return True
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise


async def update_search_vector(
    db: AsyncSession,
    document_id: str,
    title: str,
    author: str,
    description: str | None,
    extracted_text: str | None,
) -> None:
    """
    Update the search_vector for a document.

    Args:
        db: Async database session
        document_id: Document ID
        title: Document title
        author: Document author
        description: Document description
        extracted_text: Extracted text content
    """
    try:
        # Create tsvector using to_tsvector
        search_vector_expr = func.to_tsvector(
            "english",
            func.coalesce(title, "")
            + " "
            + func.coalesce(author, "")
            + " "
            + func.coalesce(description or "", "")
            + " "
            + func.coalesce(extracted_text or "", ""),
        )

        await db.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(search_vector=search_vector_expr)
        )
        logger.debug(f"Updated search vector for document: {document_id}")
    except Exception as e:
        logger.error(f"Error updating search vector: {e}")
        raise
