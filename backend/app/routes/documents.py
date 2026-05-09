"""Document-related API endpoints."""

import logging
import os
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.crud import (
    create_document,
    create_version,
    delete_document,
    extract_and_store_references,
    get_document,
    list_documents,
    update_search_vector,
    validate_version,
)
from app.database import AsyncSessionLocal
from app.models import (
    DocumentCreate,
    DocumentListResponse,
    DocumentWithLatestVersion,
    ErrorResponse,
    MessageResponse,
    ValidationRequest,
    VersionResponse,
)
from app.processors import process_document
from app.storage import download_file, upload_file

logger = logging.getLogger(__name__)

# File validation constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}


def validate_file_type(file: UploadFile) -> None:
    """Validate file type by extension and MIME type.

    Args:
        file: UploadFile to validate

    Raises:
        HTTPException: If file type is not allowed
    """
    # Check file extension
    if file.filename is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File filename is required",
        )

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension: {file_ext}. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )


def validate_file_size(file: UploadFile) -> None:
    """Validate file size.

    Args:
        file: UploadFile to validate

    Raises:
        HTTPException: If file is too large
    """
    # Read file content to check size
    content = file.file.read()
    file.file.seek(0)  # Reset file pointer

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)} MB",
        )


router = APIRouter(prefix="/documents", tags=["Documents"])


# Database session dependency
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.post(
    "/upload",
    response_model=DocumentWithLatestVersion,
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Upload a document",
    description="Upload a PDF or Word document, creating its first version with Markdown conversion.",
)
async def upload_document(
    db: DbSession,
    file: UploadFile = File(..., description="Document file (PDF or Word)"),
    title: str = Form(..., min_length=1, max_length=255),
    author: str = Form(..., min_length=1, max_length=255),
    description: str = Form(None, max_length=2000),
) -> DocumentWithLatestVersion:
    """Upload a document (PDF/Word) and create its first version.

    The document is:
    1. Stored in MinIO
    2. Processed to extract text and convert to Markdown
    3. Metadata saved to PostgreSQL
    """
    try:
        # Validate file type and extension
        validate_file_type(file)

        # Validate file size
        validate_file_size(file)

        # Read file content
        file_data = await file.read()

        # Re-validate extension after reading (defensive)
        filename = file.filename or ""
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_ext}",
            )

        # Create document record
        doc_create = DocumentCreate(
            title=title,
            author=author,
            description=description,
        )
        document_response = await create_document(db, doc_create)
        doc_id = str(document_response.id)

        # Generate storage paths
        version_num = 1
        raw_path = f"{doc_id}/v{version_num}/{filename}"
        md_path = f"{doc_id}/v{version_num}/document.md"

        # Process document (extract text + convert to Markdown)
        extracted_text, markdown_content = await process_document(file_data, filename)

        # Upload raw file to MinIO
        await upload_file(
            bucket=settings.minio_bucket,
            object_name=raw_path,
            file_data=file_data,
        )

        # Upload Markdown file to MinIO
        await upload_file(
            bucket=settings.minio_bucket,
            object_name=md_path,
            file_data=markdown_content,
        )

        # Create version record with extracted text
        version_data = {
            "filename": file.filename,
            "file_type": file_ext.lstrip(".").upper(),
            "file_size": len(file_data),
            "storage_path": raw_path,
            "markdown_path": md_path,
            "extracted_text": extracted_text,
        }
        version_response = await create_version(db, doc_id, version_data)

        # Update search vector for the document
        await update_search_vector(
            db,
            doc_id,
            doc_create.title,
            doc_create.author,
            doc_create.description,
            extracted_text,
        )

        # Extract and store references from the document text
        try:
            await extract_and_store_references(
                db,
                doc_id,
                extracted_text,
                version_num,
            )
        except Exception as e:
            logger.warning(f"Failed to extract references for document {doc_id}: {e}")

        logger.info(f"Document uploaded: {doc_id}, version: {version_num}")

        return DocumentWithLatestVersion(
            document=document_response,
            latest_version=version_response,
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document",
        )


@router.get(
    "",
    response_model=DocumentListResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="List all documents",
    description="List all documents with pagination support.",
)
async def list_documents_endpoint(
    db: DbSession,
    skip: int = 0,
    limit: int = 100,
) -> DocumentListResponse:
    """List all documents with pagination.

    Query parameters:
    - skip: Number of documents to skip (default: 0)
    - limit: Maximum number of documents to return (default: 100)
    """
    try:
        result = await list_documents(db, skip=skip, limit=limit)
        return result
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents",
        )


@router.get(
    "/{document_id}",
    response_model=DocumentWithLatestVersion,
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get document by ID",
    description="Retrieve document metadata and its latest version.",
)
async def get_document_endpoint(
    db: DbSession,
    document_id: str,
) -> DocumentWithLatestVersion:
    """Get document metadata and its latest version."""
    try:
        result = await get_document(db, document_id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found",
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch document",
        )


@router.delete(
    "/{document_id}",
    response_model=MessageResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Delete a document",
    description="Delete a document and all its associated data (versions, references, storage files).",
)
async def delete_document_endpoint(
    db: DbSession,
    document_id: str,
) -> MessageResponse:
    """Delete a document and all its associated data (versions, references)."""
    try:
        success = await delete_document(db, document_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found",
            )
        return MessageResponse(message=f"Document {document_id} deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document",
        )


@router.post(
    "/{document_id}/validate",
    response_model=VersionResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Document or version not found"},
        400: {"model": ErrorResponse, "description": "Version already validated"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Validate document version",
    description="Mark the latest version of a document as validated.",
)
async def validate_document_endpoint(
    db: DbSession,
    document_id: str,
    validation_data: ValidationRequest,
) -> VersionResponse:
    """Mark the latest version of a document as validated."""
    try:
        # Get document with latest version
        doc_with_version = await get_document(db, document_id)
        if doc_with_version is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found",
            )

        if doc_with_version.latest_version is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} has no versions",
            )

        version_id = str(doc_with_version.latest_version.id)
        result = await validate_version(db, version_id, validation_data)
        logger.info(f"Validated version {version_id} for document {document_id}")
        return result

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate document",
        )


@router.get(
    "/{document_id}/markdown",
    responses={
        404: {"model": ErrorResponse, "description": "Document or Markdown not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Download Markdown",
    description="Download the Markdown version of the latest document version.",
)
async def download_markdown(
    document_id: str,
    db: DbSession,
) -> StreamingResponse:
    """Download the Markdown version of the latest document version."""
    try:
        # Get document to find latest version markdown path
        doc_with_version = await get_document(db, document_id)
        if doc_with_version is None or doc_with_version.latest_version is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found or has no versions",
            )

        md_path = doc_with_version.latest_version.markdown_path
        if md_path is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Markdown file not available",
            )

        # Download from MinIO
        markdown_content = await download_file(
            bucket=settings.minio_bucket,
            object_name=md_path,
        )

        logger.debug(f"Downloaded Markdown for document: {document_id}")

        # Return as streaming response
        return StreamingResponse(
            iter([markdown_content]),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=document_{document_id}.md"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Markdown download error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download Markdown",
        )


@router.get(
    "/{document_id}/download",
    responses={
        404: {"model": ErrorResponse, "description": "Document or file not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Download original file",
    description="Download the original document file of the latest version.",
)
async def download_document(
    document_id: str,
    db: DbSession,
) -> StreamingResponse:
    """Download the original document file of the latest version."""
    try:
        # Get document to find latest version storage path
        doc_with_version = await get_document(db, document_id)
        if doc_with_version is None or doc_with_version.latest_version is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found or has no versions",
            )

        storage_path = doc_with_version.latest_version.storage_path
        if storage_path is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document file not available",
            )

        # Download from MinIO
        file_content = await download_file(
            bucket=settings.minio_bucket,
            object_name=storage_path,
        )

        filename = doc_with_version.latest_version.filename
        logger.debug(f"Downloaded document file for document: {document_id}")

        # Return as streaming response with original filename
        return StreamingResponse(
            iter([file_content]),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document download error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download document",
        )
