"""CRUD operations for DryDocs.

This package contains all database CRUD operations split by entity type:
- documents: Document CRUD operations
- versions: Version CRUD operations
- references: Reference CRUD operations
- search: Search operations
"""

# Re-export all functions for backward compatibility

from app.crud.documents import (
    create_document,
    delete_document,
    get_document,
    list_documents,
    update_search_vector,
)
from app.crud.references import (
    create_reference,
    extract_and_store_references,
    get_linked_documents,
    get_references_by_source,
    get_references_by_target,
)
from app.crud.search import search_documents
from app.crud.versions import create_version, get_version, validate_version

__all__ = [
    # Documents
    "create_document",
    "get_document",
    "list_documents",
    "delete_document",
    "update_search_vector",
    # Versions
    "create_version",
    "get_version",
    "validate_version",
    # References
    "create_reference",
    "get_references_by_source",
    "get_references_by_target",
    "get_linked_documents",
    "extract_and_store_references",
    # Search
    "search_documents",
]
