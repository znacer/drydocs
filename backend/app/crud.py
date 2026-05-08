"""Database CRUD operations."""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import Document, Version
from app.models import (
    DocumentCreate,
    DocumentListResponse,
    DocumentResponse,
    DocumentWithLatestVersion,
    ValidationRequest,
    VersionResponse,
)

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


async def list_documents(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> DocumentListResponse:
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
            select(Document)
            .offset(skip)
            .limit(limit)
            .order_by(Document.created_at.desc())
        )
        db_documents = result.scalars().all()

        documents = [DocumentResponse.model_validate(doc) for doc in db_documents]

        return DocumentListResponse(documents=documents, count=total_count)
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise


async def create_version(
    db: AsyncSession,
    document_id: str,
    version_data: dict,
) -> VersionResponse:
    """
    Create a new version for a document.

    Args:
        db: Async database session
        document_id: Parent document ID
        version_data: Version data dictionary with filename, file_type, file_size, storage_path, markdown_path

    Returns:
        Created version as VersionResponse
    """
    try:
        # Get current max version number
        result = await db.execute(
            select(func.coalesce(func.max(Version.version_number), 0)).where(
                Version.document_id == document_id
            )
        )
        max_version = result.scalar_one()
        new_version_number = max_version + 1

        version_id = str(uuid.uuid4())
        db_version = Version(
            id=version_id,
            document_id=document_id,
            version_number=new_version_number,
            filename=version_data["filename"],
            file_type=version_data["file_type"],
            file_size=version_data["file_size"],
            storage_path=version_data["storage_path"],
            markdown_path=version_data.get("markdown_path"),
            is_valid=False,
        )
        db.add(db_version)
        await db.flush()

        # Update document's current_version
        await db.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(current_version=new_version_number)
        )

        await db.refresh(db_version)
        logger.debug(f"Created version {new_version_number} for document: {document_id}")

        return VersionResponse.model_validate(db_version)
    except Exception as e:
        logger.error(f"Error creating version: {e}")
        raise


async def validate_version(
    db: AsyncSession,
    version_id: str,
    validation_data: ValidationRequest,
) -> VersionResponse:
    """
    Mark a version as validated.

    Args:
        db: Async database session
        version_id: Version ID to validate
        validation_data: Validation request data

    Returns:
        Updated version as VersionResponse

    Raises:
        ValueError: If version is already validated
    """
    try:
        result = await db.execute(select(Version).where(Version.id == version_id))
        db_version = result.scalar_one_or_none()

        if db_version is None:
            logger.error(f"Version not found: {version_id}")
            raise ValueError(f"Version {version_id} not found")

        if db_version.is_valid:
            logger.warning(f"Version {version_id} is already validated")
            raise ValueError(f"Version {version_id} is already validated")

        await db.execute(
            update(Version)
            .where(Version.id == version_id)
            .values(
                is_valid=True,
                validated_by=str(validation_data.user_id),
                validation_notes=validation_data.notes,
                validated_at=datetime.now(UTC),
            )
        )

        # Update document status to "valid" if this is the latest version
        doc_result = await db.execute(select(Document).where(Document.id == db_version.document_id))
        db_document = doc_result.scalar_one()
        if db_document.current_version == db_version.version_number:
            await db.execute(
                update(Document).where(Document.id == db_version.document_id).values(status="valid")
            )

        await db.refresh(db_version)
        logger.debug(f"Validated version: {version_id}")

        return VersionResponse.model_validate(db_version)
    except Exception as e:
        logger.error(f"Error validating version: {e}")
        raise


async def get_version(db: AsyncSession, version_id: str) -> VersionResponse | None:
    """
    Get a specific version by ID.

    Args:
        db: Async database session
        version_id: Version ID

    Returns:
        VersionResponse or None if not found
    """
    try:
        result = await db.execute(select(Version).where(Version.id == version_id))
        db_version = result.scalar_one_or_none()
        if db_version is None:
            return None
        return VersionResponse.model_validate(db_version)
    except Exception as e:
        logger.error(f"Error fetching version: {e}")
        raise
