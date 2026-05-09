"""Pydantic schemas for request/response models."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# --- Document Schemas ---


class DocumentBase(BaseModel):
    """Base document schema with common fields."""

    title: str = Field(..., min_length=1, max_length=255, description="Document title")
    author: str = Field(..., min_length=1, max_length=255, description="Document author")
    description: str | None = Field(None, max_length=2000, description="Document description")


class DocumentCreate(DocumentBase):
    """Schema for creating a document (includes file metadata)."""

    pass


class DocumentResponse(BaseModel):
    """Response schema for document metadata."""

    id: UUID
    title: str
    author: str
    description: str | None
    current_version: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Version Schemas ---


class VersionBase(BaseModel):
    """Base version schema."""

    version_number: int
    filename: str
    file_type: str
    file_size: int
    is_valid: bool = False


class VersionCreate(VersionBase):
    """Schema for creating a version."""

    storage_path: str
    markdown_path: str | None = None


class VersionResponse(BaseModel):
    """Response schema for version metadata."""

    id: UUID
    document_id: UUID
    version_number: int
    filename: str
    file_type: str
    file_size: int
    storage_path: str
    markdown_path: str | None
    is_valid: bool
    validated_by: UUID | None
    validation_notes: str | None
    validated_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Combined Schemas ---


class DocumentWithLatestVersion(BaseModel):
    """Document with its latest version."""

    document: DocumentResponse
    latest_version: VersionResponse | None = None


class DocumentListResponse(BaseModel):
    """Response schema for listing documents."""

    documents: list[DocumentResponse]
    count: int


# --- Validation Schemas ---


class ValidationRequest(BaseModel):
    """Request schema for validating a version."""

    user_id: UUID = Field(..., description="ID of the user validating the document")
    notes: str | None = Field(None, max_length=2000, description="Validation notes")


class ValidationResponse(VersionResponse):
    """Response after validation."""

    pass


# --- Error Schemas ---


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    error_type: str | None = None


# --- Search Schemas ---


class SearchRequest(BaseModel):
    """Request schema for searching documents."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    limit: int = Field(20, ge=1, le=100, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")


class SearchResult(BaseModel):
    """A single search result."""

    id: UUID
    title: str
    author: str
    description: str | None
    current_version: int
    status: str
    created_at: datetime
    updated_at: datetime
    score: float = Field(description="Search relevance score (rank)")
    highlight: str | None = Field(None, description="Highlighted text snippet")

    model_config = ConfigDict(from_attributes=True)


class SearchResponse(BaseModel):
    """Response schema for search results."""

    results: list[SearchResult]
    count: int
    total: int


# --- Reference Schemas ---


class ReferenceCreate(BaseModel):
    """Schema for creating a document reference."""

    source_document_id: UUID = Field(..., description="ID of the source document")
    referenced_document_id: UUID = Field(..., description="ID of the referenced document")
    reference_text: str = Field(
        ..., max_length=500, description="The text that references another document"
    )
    reference_type: str = Field(
        default="inline", description="Type of reference (inline, citation, etc.)"
    )
    version_number: int = Field(
        default=1, ge=1, description="Version number of the source document"
    )


class ReferenceResponse(BaseModel):
    """Response schema for a document reference."""

    id: UUID
    source_document_id: UUID
    referenced_document_id: UUID
    reference_text: str
    reference_type: str
    version_number: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentWithReferences(BaseModel):
    """Document with its references."""

    document: DocumentResponse
    referenced_documents: list[ReferenceResponse] = Field(default_factory=list)
    referencing_documents: list[ReferenceResponse] = Field(default_factory=list)


class ExtractReferencesRequest(BaseModel):
    """Request to extract references from a document's text."""

    document_id: UUID = Field(..., description="ID of the document to extract references from")
    version_number: int | None = Field(None, ge=1, description="Specific version to extract from")


class ExtractReferencesResponse(BaseModel):
    """Response with extracted references."""

    document_id: UUID
    version_number: int
    extracted_references: list[str] = Field(
        default_factory=list, description="List of extracted reference strings"
    )
    found_references: list[ReferenceResponse] = Field(
        default_factory=list, description="References that match existing documents"
    )
    unmatched_references: list[str] = Field(
        default_factory=list, description="References that don't match any documents"
    )


class LinkedDocumentsResponse(BaseModel):
    """Response with documents linked to/from a given document."""

    document: DocumentResponse
    referenced_documents: list[DocumentResponse] = Field(
        default_factory=list, description="Documents referenced by this document"
    )
    referencing_documents: list[DocumentResponse] = Field(
        default_factory=list, description="Documents that reference this document"
    )


class MessageResponse(BaseModel):
    """Simple response with a message."""

    message: str
    success: bool = True
