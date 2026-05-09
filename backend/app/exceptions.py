"""Custom exception hierarchy for the DryDocs backend."""

from typing import Any


# Base exception for all application errors
class DryDocsError(Exception):
    """Base exception for all DryDocs application errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


# Document-related exceptions
class DocumentError(DryDocsError):
    """Base exception for document-related errors."""

    pass


class DocumentNotFoundError(DocumentError):
    """Raised when a document is not found."""

    def __init__(self, document_id: str) -> None:
        super().__init__(f"Document not found: {document_id}", {"document_id": document_id})
        self.document_id = document_id


class DocumentAlreadyExistsError(DocumentError):
    """Raised when attempting to create a document that already exists."""

    def __init__(self, document_id: str | None = None, title: str | None = None) -> None:
        message = f"Document already exists: {document_id or title or 'unknown'}"
        super().__init__(message, {"document_id": document_id, "title": title})


class InvalidDocumentTypeError(DocumentError):
    """Raised when an unsupported document type is provided."""

    def __init__(self, file_type: str, supported: list[str]) -> None:
        super().__init__(
            f"Unsupported document type: {file_type}. Supported: {', '.join(supported)}",
            {"file_type": file_type, "supported": supported},
        )
        self.file_type = file_type
        self.supported = supported


# Version-related exceptions
class VersionError(DryDocsError):
    """Base exception for version-related errors."""

    pass


class VersionNotFoundError(VersionError):
    """Raised when a version is not found."""

    def __init__(self, version_id: str) -> None:
        super().__init__(f"Version not found: {version_id}", {"version_id": version_id})
        self.version_id = version_id


class VersionAlreadyValidatedError(VersionError):
    """Raised when attempting to validate an already validated version."""

    def __init__(self, version_id: str) -> None:
        super().__init__(
            f"Version already validated: {version_id}",
            {"version_id": version_id},
        )
        self.version_id = version_id


# Storage-related exceptions
class StorageError(DryDocsError):
    """Base exception for storage-related errors."""

    pass


class StorageUploadError(StorageError):
    """Raised when file upload to storage fails."""

    def __init__(self, object_name: str, reason: str) -> None:
        super().__init__(
            f"Failed to upload file: {object_name}. Reason: {reason}",
            {"object_name": object_name, "reason": reason},
        )
        self.object_name = object_name
        self.reason = reason


class StorageDownloadError(StorageError):
    """Raised when file download from storage fails."""

    def __init__(self, object_name: str, reason: str) -> None:
        super().__init__(
            f"Failed to download file: {object_name}. Reason: {reason}",
            {"object_name": object_name, "reason": reason},
        )
        self.object_name = object_name
        self.reason = reason


class StorageDeleteError(StorageError):
    """Raised when file deletion from storage fails."""

    def __init__(self, object_name: str, reason: str) -> None:
        super().__init__(
            f"Failed to delete file: {object_name}. Reason: {reason}",
            {"object_name": object_name, "reason": reason},
        )
        self.object_name = object_name
        self.reason = reason


# Processing-related exceptions
class ProcessingError(DryDocsError):
    """Base exception for document processing errors."""

    pass


class TextExtractionError(ProcessingError):
    """Raised when text extraction from a document fails."""

    def __init__(self, filename: str, reason: str) -> None:
        super().__init__(
            f"Failed to extract text from: {filename}. Reason: {reason}",
            {"filename": filename, "reason": reason},
        )
        self.filename = filename
        self.reason = reason


class MarkdownConversionError(ProcessingError):
    """Raised when Markdown conversion fails."""

    def __init__(self, filename: str, reason: str) -> None:
        super().__init__(
            f"Failed to convert to Markdown: {filename}. Reason: {reason}",
            {"filename": filename, "reason": reason},
        )
        self.filename = filename
        self.reason = reason


# Search-related exceptions
class SearchError(DryDocsError):
    """Base exception for search-related errors."""

    pass


class InvalidSearchQueryError(SearchError):
    """Raised when a search query is invalid."""

    def __init__(self, query: str, reason: str) -> None:
        super().__init__(
            f"Invalid search query: {query}. Reason: {reason}",
            {"query": query, "reason": reason},
        )
        self.query = query
        self.reason = reason


# Reference-related exceptions
class ReferenceError(DryDocsError):
    """Base exception for reference-related errors."""

    pass


class ReferenceNotFoundError(ReferenceError):
    """Raised when a reference is not found."""

    def __init__(self, reference_id: str) -> None:
        super().__init__(
            f"Reference not found: {reference_id}",
            {"reference_id": reference_id},
        )
        self.reference_id = reference_id


class CircularReferenceError(ReferenceError):
    """Raised when a circular reference is detected."""

    def __init__(self, document_id: str, referenced_id: str) -> None:
        super().__init__(
            f"Circular reference detected: {document_id} -> {referenced_id}",
            {"document_id": document_id, "referenced_id": referenced_id},
        )
        self.document_id = document_id
        self.referenced_id = referenced_id


# Validation-related exceptions
class ValidationError(DryDocsError):
    """Base exception for validation-related errors."""

    pass


class ValidationFailedError(ValidationError):
    """Raised when validation fails."""

    def __init__(self, version_id: str, reason: str) -> None:
        super().__init__(
            f"Validation failed for version: {version_id}. Reason: {reason}",
            {"version_id": version_id, "reason": reason},
        )
        self.version_id = version_id
        self.reason = reason
