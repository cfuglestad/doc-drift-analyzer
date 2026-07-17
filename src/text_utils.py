"""Text normalization and segmentation helpers."""

import re


def clean_text(text: str) -> str:
    """Normalize line endings and repeated horizontal or vertical whitespace."""
    text = text.replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def split_into_paragraphs(text: str) -> list[str]:
    """Split text on blank lines, retaining a fallback for unsplit input."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return paragraphs if paragraphs else [text.strip()]


def split_into_sentences(text: str) -> list[str]:
    """Split normalized text at basic sentence-ending punctuation."""
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
