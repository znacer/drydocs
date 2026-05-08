"""Document processing: text extraction and Markdown conversion."""

import logging
import os
import subprocess
import tempfile
from pathlib import Path

from docx import Document as DocxDocument
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)


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
