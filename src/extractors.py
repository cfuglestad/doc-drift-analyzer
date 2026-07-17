"""Text extraction adapters for supported document formats."""

import io
from typing import Protocol

from docx import Document
from pypdf import PdfReader


class UploadedFile(Protocol):
    """Minimal interface required from an uploaded document."""

    name: str

    def read(self) -> bytes:
        """Read the uploaded file content."""
        ...


def extract_text_from_txt(file_bytes: bytes) -> str:
    """Decode UTF-8 text bytes while ignoring invalid byte sequences."""
    return file_bytes.decode("utf-8", errors="ignore")


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract and join text from each page of a PDF document."""
    reader = PdfReader(io.BytesIO(file_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract and join paragraph text from a Word document."""
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs)


def extract_text(uploaded_file: UploadedFile | None) -> str:
    """Dispatch an uploaded file to its format-specific extractor."""
    if uploaded_file is None:
        return ""

    file_bytes = uploaded_file.read()
    name = uploaded_file.name.lower()

    if name.endswith(".txt"):
        return extract_text_from_txt(file_bytes)
    if name.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    if name.endswith(".docx"):
        return extract_text_from_docx(file_bytes)

    return extract_text_from_txt(file_bytes)
