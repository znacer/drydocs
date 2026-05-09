"""Document processing: text extraction and Markdown conversion."""

import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path

from docx import Document as DocxDocument
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

# Patterns for extracting document references
REFERENCE_PATTERNS = [
    # Pattern for [Doc-ID] or [DOC-ID] style references
    r"\[([Dd][Oo][Cc][-_]?\d+)\]",
    # Pattern for See: Document X or See Document X
    r"(?:See|see|SEEN|Reference|reference|Ref|ref):?\s*(?:Document|Doc|doc|DOc|DOC)\s*([A-Za-z\d\s-]+)",
    # Pattern for Document "Title" or Document 'Title'
    r"(?:Document|Doc|doc)\s*[\"']([^\"']+)[\"']",
    # Pattern for #ID style references
    r"#(\d+)",
    # Pattern for Doc-123 or DOC-123
    r"(?:Doc|DOC|document|DOCUMENT)[-_](\d+)",
]

# Compiled patterns for efficiency
COMPILED_PATTERNS = [re.compile(pattern) for pattern in REFERENCE_PATTERNS]


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file.

    Args:
        file_path: Path to the PDF file

    Returns:
        Extracted text as string
    """
    try:
        with open(file_path, "rb") as file:
            reader = PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
    except Exception as e:
        logger.error(f"PDF text extraction error: {e}")
        raise ValueError(f"Failed to extract text from PDF: {e}")


def extract_text_from_docx(file_path: str) -> str:
    """
    Extract text from a Word (.docx) file.

    Args:
        file_path: Path to the DOCX file

    Returns:
        Extracted text as string
    """
    try:
        doc = DocxDocument(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"DOCX text extraction error: {e}")
        raise ValueError(f"Failed to extract text from DOCX: {e}")


def extract_text(file_path: str) -> str:
    """
    Extract text from a document file (PDF or Word).

    Args:
        file_path: Path to the file

    Returns:
        Extracted text as string

    Raises:
        ValueError: If file type is not supported or extraction fails
    """
    file_ext = Path(file_path).suffix.lower()

    if file_ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif file_ext in (".docx", ".doc"):
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_ext}")


def convert_to_markdown(input_path: str, output_path: str) -> None:
    """
    Convert a document to Markdown using pandoc.

    Args:
        input_path: Path to the input file
        output_path: Path to save the Markdown output

    Raises:
        RuntimeError: If pandoc conversion fails
    """
    try:
        subprocess.run(
            ["pandoc", input_path, "-o", output_path, "-t", "markdown"],
            check=True,
            capture_output=True,
        )
        logger.debug(f"Converted {input_path} to Markdown at {output_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Pandoc conversion error: {e.stderr.decode()}")
        raise RuntimeError(f"Failed to convert document to Markdown: {e.stderr.decode()}")
    except FileNotFoundError:
        logger.error("Pandoc not found. Please install pandoc on your system.")
        raise RuntimeError("Pandoc is not installed. Please install pandoc.")


async def process_document(file_data: bytes, filename: str) -> tuple[str, bytes]:
    """
    Process a document: extract text and convert to Markdown.

    Args:
        file_data: Raw file bytes
        filename: Original filename

    Returns:
        Tuple of (extracted_text, markdown_content)

    Raises:
        ValueError: If file type is unsupported
        RuntimeError: If processing fails
    """
    file_ext = Path(filename).suffix.lower()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Save original file
        input_path = os.path.join(temp_dir, filename)
        with open(input_path, "wb") as f:
            f.write(file_data)

        # Extract text
        extracted_text = extract_text(input_path)

        # Convert to Markdown
        markdown_path = os.path.join(temp_dir, "document.md")

        # For PDF, use text extraction directly and format as Markdown
        # For Word, use pandoc for better formatting
        if file_ext == ".pdf":
            # PDF: pandoc can't read PDF by default, so we use extracted text
            # and create a simple Markdown document
            with open(markdown_path, "w", encoding="utf-8") as f:
                f.write(f"# {Path(filename).stem}\n\n")
                f.write(extracted_text)
        else:
            # Word documents: use pandoc for conversion
            convert_to_markdown(input_path, markdown_path)

        # Read Markdown content
        with open(markdown_path, "rb") as f:
            markdown_content = f.read()

        return extracted_text, markdown_content


def extract_references(text: str, existing_document_ids: list[str] | None = None) -> list[str]:
    """
    Extract potential document references from text.

    Args:
        text: The text to search for references
        existing_document_ids: Optional list of existing document IDs to filter matches

    Returns:
        List of extracted reference strings
    """
    references: set[str] = set()

    for pattern in COMPILED_PATTERNS:
        matches = pattern.finditer(text)
        for match in matches:
            # Get all captured groups
            for group_idx in range(1, len(match.groups()) + 1):
                group_value = match.group(group_idx)
                if group_value:
                    references.add(group_value.strip())

    # Also try to find UUID-like patterns
    uuid_pattern = re.compile(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE
    )
    uuid_matches = uuid_pattern.finditer(text)
    for match in uuid_matches:
        references.add(match.group())

    # Filter to only existing document IDs if provided
    references_list = list(references)
    if existing_document_ids:
        existing_ids_set = set(existing_document_ids)
        references_list = [ref for ref in references_list if ref in existing_ids_set]

    return references_list


def extract_all_references(text: str) -> list[str]:
    """
    Extract all potential document references from text without filtering.

    Args:
        text: The text to search for references

    Returns:
        List of all extracted reference strings (including non-matching ones)
    """
    references: set[str] = set()

    for pattern in COMPILED_PATTERNS:
        matches = pattern.finditer(text)
        for match in matches:
            for group_idx in range(1, len(match.groups()) + 1):
                group_value = match.group(group_idx)
                if group_value:
                    references.add(group_value.strip())

    # Also try to find UUID-like patterns
    uuid_pattern = re.compile(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE
    )
    uuid_matches = uuid_pattern.finditer(text)
    for match in uuid_matches:
        references.add(match.group())

    return list(references)


def create_search_vector(
    title: str, author: str, description: str | None, extracted_text: str | None
) -> str:
    """
    Create a PostgreSQL tsvector string for full-text search.

    Args:
        title: Document title
        author: Document author
        description: Document description (optional)
        extracted_text: Extracted text content (optional)

    Returns:
        String representation of tsvector for PostgreSQL
    """
    # Build the text to be vectorized
    text_parts = [title, author]
    if description:
        text_parts.append(description)
    if extracted_text:
        text_parts.append(extracted_text)

    # Create tsvector using to_tsvector function
    # Weight: A (title) > B (author) > C (description) > D (content)
    return f"to_tsvector('english', coalesce({repr(title)}, '') || ' ' || coalesce({repr(author)}, '') || ' ' || coalesce({repr(description or '')}, '') || ' ' || coalesce({repr(extracted_text or '')}, ''))"
