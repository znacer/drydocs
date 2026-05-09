"""Reference CRUD operations."""

import logging
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import Document, DocumentReference
from app.models import (
    DocumentResponse,
    ExtractReferencesResponse,
    LinkedDocumentsResponse,
    ReferenceCreate,
    ReferenceResponse,
)

if TYPE_CHECKING:
    from uuid import UUID

logger = logging.getLogger(__name__)


async def create_reference(db: AsyncSession, reference_data: ReferenceCreate) -> ReferenceResponse:
    """
    Create a new document reference.

    Args:
        db: Async database session
        reference_data: Reference data

    Returns:
        Created reference as ReferenceResponse
    """
    try:
        ref_id = str(uuid.uuid4())
        db_reference = DocumentReference(
            id=ref_id,
            source_document_id=str(reference_data.source_document_id),
            referenced_document_id=str(reference_data.referenced_document_id),
            reference_text=reference_data.reference_text,
            reference_type=reference_data.reference_type,
            version_number=reference_data.version_number,
        )
        db.add(db_reference)
        await db.flush()
        await db.refresh(db_reference)

        logger.debug(f"Created reference: {ref_id}")
        return ReferenceResponse.model_validate(db_reference)
    except Exception as e:
        logger.error(f"Error creating reference: {e}")
        raise


async def get_references_by_source(
    db: AsyncSession, source_document_id: str
) -> list[ReferenceResponse]:
    """
    Get all references from a source document.

    Args:
        db: Async database session
        source_document_id: Source document ID

    Returns:
        List of references from the source document
    """
    try:
        result = await db.execute(
            select(DocumentReference)
            .where(DocumentReference.source_document_id == source_document_id)
            .order_by(DocumentReference.created_at)
        )
        db_references = result.scalars().all()
        return [ReferenceResponse.model_validate(ref) for ref in db_references]
    except Exception as e:
        logger.error(f"Error fetching references by source: {e}")
        raise


async def get_references_by_target(
    db: AsyncSession, referenced_document_id: str
) -> list[ReferenceResponse]:
    """
    Get all references pointing to a document.

    Args:
        db: Async database session
        referenced_document_id: Referenced document ID

    Returns:
        List of references pointing to the document
    """
    try:
        result = await db.execute(
            select(DocumentReference)
            .where(DocumentReference.referenced_document_id == referenced_document_id)
            .order_by(DocumentReference.created_at)
        )
        db_references = result.scalars().all()
        return [ReferenceResponse.model_validate(ref) for ref in db_references]
    except Exception as e:
        logger.error(f"Error fetching references by target: {e}")
        raise


async def get_linked_documents(db: AsyncSession, document_id: str) -> LinkedDocumentsResponse:
    """
    Get all documents linked to/from a given document.

    Args:
        db: Async database session
        document_id: Document ID

    Returns:
        LinkedDocumentsResponse with referenced and referencing documents
    """
    try:
        # Get the source document
        doc_result = await db.execute(select(Document).where(Document.id == document_id))
        db_document = doc_result.scalar_one_or_none()

        if db_document is None:
            logger.error(f"Document not found: {document_id}")
            raise ValueError(f"Document {document_id} not found")

        # Get documents referenced by this document
        ref_result = await db.execute(
            select(DocumentReference)
            .where(DocumentReference.source_document_id == document_id)
            .options(selectinload(DocumentReference.referenced_document))
        )
        outgoing_references = ref_result.scalars().all()
        referenced_documents = [
            DocumentResponse.model_validate(ref.referenced_document)
            for ref in outgoing_references
            if ref.referenced_document
        ]

        # Get documents that reference this document
        incoming_ref_result = await db.execute(
            select(DocumentReference)
            .where(DocumentReference.referenced_document_id == document_id)
            .options(selectinload(DocumentReference.source_document))
        )
        incoming_references = incoming_ref_result.scalars().all()
        referencing_documents = [
            DocumentResponse.model_validate(ref.source_document)
            for ref in incoming_references
            if ref.source_document
        ]

        return LinkedDocumentsResponse(
            document=DocumentResponse.model_validate(db_document),
            referenced_documents=referenced_documents,
            referencing_documents=referencing_documents,
        )
    except Exception as e:
        logger.error(f"Error fetching linked documents: {e}")
        raise


async def extract_and_store_references(
    db: AsyncSession,
    document_id: str,
    extracted_text: str,
    version_number: int = 1,
) -> ExtractReferencesResponse:
    """
    Extract references from document text and store them.

    Args:
        db: Async database session
        document_id: Document ID
        extracted_text: Text to extract references from
        version_number: Version number of the document

    Returns:
        ExtractReferencesResponse with extraction results
    """
    from app.processors import extract_all_references

    try:
        # Get all existing document IDs for matching
        all_docs_result = await db.execute(select(Document.id))
        all_document_ids = [str(row[0]) for row in all_docs_result.all()]

        # Extract all references from text
        all_references = extract_all_references(extracted_text)

        # Filter to only valid document IDs
        matched_document_ids = [ref for ref in all_references if ref in all_document_ids]

        # Remove duplicates while preserving order
        seen = set()
        unique_matched_ids = []
        for ref_id in matched_document_ids:
            if ref_id not in seen:
                seen.add(ref_id)
                unique_matched_ids.append(ref_id)

        # Store the references
        created_references: list[ReferenceResponse] = []
        for ref_id in unique_matched_ids:
            try:
                reference_data = ReferenceCreate(
                    source_document_id=UUID(document_id),
                    referenced_document_id=UUID(ref_id),
                    reference_text=f"[Doc-{ref_id}]",
                    reference_type="inline",
                    version_number=version_number,
                )

                ref_response = await create_reference(db, reference_data)
                created_references.append(ref_response)
            except Exception as e:
                logger.warning(f"Failed to create reference to {ref_id}: {e}")
                continue

        return ExtractReferencesResponse(
            document_id=UUID(document_id),
            version_number=version_number,
            extracted_references=all_references,
            found_references=created_references,
            unmatched_references=[ref for ref in all_references if ref not in all_document_ids],
        )
    except Exception as e:
        logger.error(f"Error extracting and storing references: {e}")
        raise
