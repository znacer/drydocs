"""Document reference-related API endpoints."""

import logging
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    extract_and_store_references,
    get_document,
    get_linked_documents,
    get_references_by_source,
    get_references_by_target,
)
from app.database import AsyncSessionLocal, Version
from app.models import (
    ErrorResponse,
    ExtractReferencesResponse,
    LinkedDocumentsResponse,
    ReferenceResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["References"])


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


@router.get(
    "/documents/{document_id}/references",
    response_model=LinkedDocumentsResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get all document references",
    description="Get all documents referenced by and referencing the given document.",
)
async def get_document_references_endpoint(
    db: DbSession,
    document_id: str,
) -> LinkedDocumentsResponse:
    """Get all documents referenced by and referencing the given document.

    Returns:
        - referenced_documents: Documents that this document references
        - referencing_documents: Documents that reference this document
    """
    try:
        result = await get_linked_documents(db, document_id)
        return result
    except HTTPException:
        raise
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error fetching references: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch document references",
        )


@router.post(
    "/documents/{document_id}/extract-references",
    response_model=ExtractReferencesResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Extract document references",
    description="Extract and store references from a document's text content.",
)
async def extract_references_endpoint(
    db: DbSession,
    document_id: str,
    version_number: int | None = None,
) -> ExtractReferencesResponse:
    """Extract and store references from a document's text content.

    Scans the document's extracted text for patterns like [Doc-123], Document X, etc.
    and creates reference links to matching documents.
    """
    try:
        # Get document with latest version
        doc_with_version = await get_document(db, document_id)
        if doc_with_version is None or doc_with_version.latest_version is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found or has no versions",
            )

        # Use specified version or latest
        target_version = version_number or doc_with_version.latest_version.version_number

        # Get the extracted text from the version
        version_result = await db.execute(
            select(Version.extracted_text).where(
                Version.document_id == document_id,
                Version.version_number == target_version,
            )
        )
        db_version = version_result.scalar_one_or_none()

        if db_version is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {target_version} not found for document {document_id}",
            )

        extracted_text = db_version or ""

        result = await extract_and_store_references(
            db,
            document_id,
            extracted_text,
            target_version,
        )

        logger.info(f"Extracted references for document {document_id}, version {target_version}")
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reference extraction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract references",
        )


@router.get(
    "/documents/{document_id}/references/outgoing",
    response_model=list[ReferenceResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get outgoing references",
    description="Get all references created by (outgoing from) a document.",
)
async def get_outgoing_references_endpoint(
    db: DbSession,
    document_id: str,
) -> list[ReferenceResponse]:
    """Get all references created by (outgoing from) a document.

    Returns references where this document is the source.
    """
    try:
        # Verify document exists
        doc_result = await get_document(db, document_id)
        if doc_result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found",
            )

        result = await get_references_by_source(db, document_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching outgoing references: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch outgoing references",
        )


@router.get(
    "/documents/{document_id}/references/incoming",
    response_model=list[ReferenceResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get incoming references",
    description="Get all references pointing to (incoming to) a document.",
)
async def get_incoming_references_endpoint(
    db: DbSession,
    document_id: str,
) -> list[ReferenceResponse]:
    """Get all references pointing to (incoming to) a document.

    Returns references where this document is the target.
    """
    try:
        # Verify document exists
        doc_result = await get_document(db, document_id)
        if doc_result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found",
            )

        result = await get_references_by_target(db, document_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching incoming references: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch incoming references",
        )
