"""Tests for custom exception classes."""


from app.exceptions import (
    CircularReferenceError,
    DocumentAlreadyExistsError,
    DocumentError,
    DocumentNotFoundError,
    DryDocsError,
    InvalidDocumentTypeError,
    InvalidSearchQueryError,
    MarkdownConversionError,
    ProcessingError,
    ReferenceError,
    ReferenceNotFoundError,
    SearchError,
    StorageDeleteError,
    StorageDownloadError,
    StorageError,
    StorageUploadError,
    TextExtractionError,
    ValidationError,
    ValidationFailedError,
    VersionAlreadyValidatedError,
    VersionError,
    VersionNotFoundError,
)


class TestDryDocsError:
    """Tests for DryDocsError base class."""

    def test_base_exception(self):
        """Test base exception with message."""
        exc = DryDocsError("Test error")
        assert str(exc) == "Test error"
        assert exc.message == "Test error"
        assert exc.details == {}

    def test_base_exception_with_details(self):
        """Test base exception with details."""
        exc = DryDocsError("Test error", {"key": "value"})
        assert str(exc) == "Test error"
        assert exc.message == "Test error"
        assert exc.details == {"key": "value"}


class TestDocumentExceptions:
    """Tests for document-related exceptions."""

    def test_document_not_found(self):
        """Test DocumentNotFoundError."""
        doc_id = "test-id"
        exc = DocumentNotFoundError(doc_id)
        assert str(exc) == f"Document not found: {doc_id}"
        assert exc.document_id == doc_id
        assert exc.details == {"document_id": doc_id}

    def test_document_already_exists_by_id(self):
        """Test DocumentAlreadyExistsError with ID."""
        doc_id = "test-id"
        exc = DocumentAlreadyExistsError(document_id=doc_id)
        assert "test-id" in str(exc)

    def test_document_already_exists_by_title(self):
        """Test DocumentAlreadyExistsError with title."""
        title = "Test Title"
        exc = DocumentAlreadyExistsError(title=title)
        assert "Test Title" in str(exc)

    def test_invalid_document_type(self):
        """Test InvalidDocumentTypeError."""
        exc = InvalidDocumentTypeError("txt", ["pdf", "docx"])
        assert "txt" in str(exc)
        assert "pdf" in str(exc)
        assert exc.file_type == "txt"
        assert exc.supported == ["pdf", "docx"]


class TestVersionExceptions:
    """Tests for version-related exceptions."""

    def test_version_not_found(self):
        """Test VersionNotFoundError."""
        version_id = "version-id"
        exc = VersionNotFoundError(version_id)
        assert str(exc) == f"Version not found: {version_id}"
        assert exc.version_id == version_id

    def test_version_already_validated(self):
        """Test VersionAlreadyValidatedError."""
        version_id = "version-id"
        exc = VersionAlreadyValidatedError(version_id)
        assert str(exc) == f"Version already validated: {version_id}"


class TestStorageExceptions:
    """Tests for storage-related exceptions."""

    def test_storage_upload_error(self):
        """Test StorageUploadError."""
        exc = StorageUploadError("file.txt", "Permission denied")
        assert "file.txt" in str(exc)
        assert "Permission denied" in str(exc)
        assert exc.object_name == "file.txt"
        assert exc.reason == "Permission denied"

    def test_storage_download_error(self):
        """Test StorageDownloadError."""
        exc = StorageDownloadError("file.txt", "Not found")
        assert "file.txt" in str(exc)
        assert "Not found" in str(exc)

    def test_storage_delete_error(self):
        """Test StorageDeleteError."""
        exc = StorageDeleteError("file.txt", "Locked")
        assert "file.txt" in str(exc)
        assert "Locked" in str(exc)


class TestProcessingExceptions:
    """Tests for processing-related exceptions."""

    def test_text_extraction_error(self):
        """Test TextExtractionError."""
        exc = TextExtractionError("file.pdf", "Corrupt file")
        assert "file.pdf" in str(exc)
        assert "Corrupt file" in str(exc)

    def test_markdown_conversion_error(self):
        """Test MarkdownConversionError."""
        exc = MarkdownConversionError("file.docx", "Pandoc not found")
        assert "file.docx" in str(exc)
        assert "Pandoc not found" in str(exc)


class TestSearchExceptions:
    """Tests for search-related exceptions."""

    def test_invalid_search_query(self):
        """Test InvalidSearchQueryError."""
        exc = InvalidSearchQueryError("bad query", "Syntax error")
        assert "bad query" in str(exc)
        assert "Syntax error" in str(exc)


class TestReferenceExceptions:
    """Tests for reference-related exceptions."""

    def test_reference_not_found(self):
        """Test ReferenceNotFoundError."""
        ref_id = "ref-id"
        exc = ReferenceNotFoundError(ref_id)
        assert str(exc) == f"Reference not found: {ref_id}"

    def test_circular_reference(self):
        """Test CircularReferenceError."""
        exc = CircularReferenceError("doc-1", "doc-2")
        assert "doc-1" in str(exc)
        assert "doc-2" in str(exc)
        assert exc.document_id == "doc-1"
        assert exc.referenced_id == "doc-2"


class TestValidationExceptions:
    """Tests for validation-related exceptions."""

    def test_validation_failed(self):
        """Test ValidationFailedError."""
        exc = ValidationFailedError("version-1", "Missing required fields")
        assert "version-1" in str(exc)
        assert "Missing required fields" in str(exc)


class TestExceptionHierarchy:
    """Tests for exception inheritance."""

    def test_document_error_is_drydocs_exception(self):
        """Test DocumentError inherits from DryDocsError."""
        exc = DocumentNotFoundError("test-id")
        assert isinstance(exc, DocumentError)
        assert isinstance(exc, DryDocsError)
        assert isinstance(exc, Exception)

    def test_version_error_is_drydocs_exception(self):
        """Test VersionError inherits from DryDocsError."""
        exc = VersionNotFoundError("test-id")
        assert isinstance(exc, VersionError)
        assert isinstance(exc, DryDocsError)

    def test_storage_error_is_drydocs_exception(self):
        """Test StorageError inherits from DryDocsError."""
        exc = StorageUploadError("file.txt", "Error")
        assert isinstance(exc, StorageError)
        assert isinstance(exc, DryDocsError)

    def test_processing_error_is_drydocs_exception(self):
        """Test ProcessingError inherits from DryDocsError."""
        exc = TextExtractionError("file.pdf", "Error")
        assert isinstance(exc, ProcessingError)
        assert isinstance(exc, DryDocsError)

    def test_search_error_is_drydocs_exception(self):
        """Test SearchError inherits from DryDocsError."""
        exc = InvalidSearchQueryError("query", "Error")
        assert isinstance(exc, SearchError)
        assert isinstance(exc, DryDocsError)

    def test_reference_error_is_drydocs_exception(self):
        """Test ReferenceError inherits from DryDocsError."""
        exc = ReferenceNotFoundError("ref-id")
        assert isinstance(exc, ReferenceError)
        assert isinstance(exc, DryDocsError)

    def test_validation_error_is_drydocs_exception(self):
        """Test ValidationError inherits from DryDocsError."""
        exc = ValidationFailedError("version-id", "Error")
        assert isinstance(exc, ValidationError)
        assert isinstance(exc, DryDocsError)
