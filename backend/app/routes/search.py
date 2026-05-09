"""Search-related API endpoints."""

import logging

from fastapi import APIRouter, HTTPException, status

from app.crud import get_document, search_documents
from app.database import DbSession
from app.models import ErrorResponse, SearchRequest, SearchResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Search"])


@router.post(
    "/search",
    response_model=SearchResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid search request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Full-text search",
    description="Search documents using PostgreSQL full-text search across title, author, description, and content.",
)
async def search_documents_endpoint(
    db: DbSession,
    search_request: SearchRequest,
) -> SearchResponse:
    """Search documents using full-text search.

    Searches across title, author, description, and extracted text content.
    Uses PostgreSQL tsvector/tsquery for efficient full-text search.
    """
    try:
        result = await search_documents(db, search_request)
        return result
    except ValueError as e:
        logger.error(f"Search validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search documents",
        )


@router.get(
    "/documents/{document_id}/search",
    response_model=SearchResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Search related documents",
    description="Search for documents related to a specific document.",
)
async def search_related_documents_endpoint(
    db: DbSession,
    document_id: str,
    query: str = "",
    limit: int = 10,
) -> SearchResponse:
    """Search for documents related to a specific document.

    Combines full-text search with reference-based relationships.
    """
    try:
        # First check if document exists
        doc_result = await get_document(db, document_id)
        if doc_result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found",
            )

        # Perform search with the query (or use document title/keywords if no query)
        search_req = SearchRequest(
            query=query or doc_result.document.title,
            limit=limit,
            offset=0,
        )
        result = await search_documents(db, search_req)

        # Filter out the document itself from results
        result.results = [r for r in result.results if str(r.id) != document_id]
        result.count = len(result.results)

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Related search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search related documents",
        )
