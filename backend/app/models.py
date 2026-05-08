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
