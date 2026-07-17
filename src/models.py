"""Shared types for document sections and their alignments."""

from typing import Literal, TypedDict

ChangeLabel = Literal[
    "Added",
    "Removed",
    "Edited (minor)",
    "Edited (major)",
    "Unchanged",
]


class Section(TypedDict):
    """A titled block of document content."""

    title: str
    content: str


class AlignmentRow(TypedDict):
    """A pair of corresponding old and new document sections."""

    old_index: int | None
    new_index: int | None
    similarity: float
    old_title: str
    new_title: str
    old_content: str
    new_content: str
