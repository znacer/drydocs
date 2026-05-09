"""Search operations."""

import logging
import re

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Document
from app.models import (
    SearchRequest,
    SearchResponse,
    SearchResult,
)

logger = logging.getLogger(__name__)


async def search_documents(db: AsyncSession, search_request: SearchRequest) -> SearchResponse:
    """
    Search documents using PostgreSQL full-text search (tsvector).

    Args:
        db: Async database session
        search_request: Search request with query, limit, and offset

    Returns:
        SearchResponse with results, count, and total
    """
    try:
        query = search_request.query
        limit = search_request.limit
        offset = search_request.offset

        # Use to_tsquery for parsing the query
        tsquery = func.to_tsquery("english", query)

        # Build the search query using @@ operator directly with to_tsquery
        search_conditions = Document.search_vector.op("@@")(tsquery)

        # Get total count of matching documents
        count_result = await db.execute(
            select(func.count()).select_from(Document).where(search_conditions)
        )
        total_count = count_result.scalar_one()

        # Get matching documents with ranking
        result = await db.execute(
            select(
                Document,
                func.ts_rank(
                    Document.search_vector,
                    tsquery,
                ).label("score"),
            )
            .where(search_conditions)
            .order_by(text("score DESC NULLS LAST"))
            .offset(offset)
            .limit(limit)
        )

        results: list[SearchResult] = []
        for row in result:
            db_doc = row[0]
            score = row[1] if row[1] is not None else 0.0

            # Create highlight snippet
            highlight = _create_highlight(db_doc, query)

            results.append(
                SearchResult(
                    id=db_doc.id,
                    title=db_doc.title,
                    author=db_doc.author,
                    description=db_doc.description,
                    current_version=db_doc.current_version,
                    status=db_doc.status,
                    created_at=db_doc.created_at,
                    updated_at=db_doc.updated_at,
                    score=float(score),
                    highlight=highlight,
                )
            )

        return SearchResponse(
            results=results,
            count=len(results),
            total=total_count,
        )
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise


def _create_highlight(db_doc: "Document", query: str) -> str | None:
    """
    Create a highlight snippet for search results.

    Args:
        db_doc: Document instance
        query: Search query

    Returns:
        Highlighted text snippet or None
    """
    try:
        # Try to highlight in description first
        if db_doc.description:
            highlight = _highlight_text(db_doc.description, query)
            if highlight:
                return highlight

        # If we had extracted_text in the document, we could highlight there too
        # For now, return None if no good highlight found
        return None
    except Exception:
        return None


def _highlight_text(text: str, query: str) -> str | None:
    """
    Highlight query terms in text using simple regex matching.

    Args:
        text: Text to highlight
        query: Search query

    Returns:
        Highlighted text or None
    """
    # Escape special regex characters in query
    safe_query = re.escape(query)
    # Find query terms in text (case insensitive)
    pattern = re.compile(r"(\b" + re.sub(r"\s+", "|", safe_query) + r"\b)", re.IGNORECASE)

    # Create highlight
    highlighted = pattern.sub(r"**\1**", text[:500])

    # Truncate and add ellipsis if needed
    if len(highlighted) > 200:
        highlighted = highlighted[:200] + "..."

    return highlighted if highlighted != text[:500] and highlighted else None
