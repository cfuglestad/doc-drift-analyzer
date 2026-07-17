"""Tests for change summary bullet generation."""

from src.models import AlignmentRow
from src.summarization import build_change_bullets


def test_build_change_bullets_describes_each_changed_row() -> None:
    rows: list[AlignmentRow] = [
        _row("", "New", "", "content", 0.0),
        _row("Old", "", "content", "", 0.0),
        _row("Policy", "Policy", "old", "new", 0.8),
        _row("Scope", "Coverage", "old", "new", 0.5),
        _row("Same", "Same", "same", "same", 1.0),
    ]

    assert build_change_bullets(rows) == [
        "Added section: New",
        "Removed section: Old",
        "Minor edits in section: Policy",
        "Major edits in section: Scope -> Coverage",
    ]


def test_build_change_bullets_uses_untitled_fallback() -> None:
    assert build_change_bullets([_row("", "", "", "new", 0.0)]) == ["Added section: Untitled"]


def _row(
    old_title: str,
    new_title: str,
    old_content: str,
    new_content: str,
    similarity: float,
) -> AlignmentRow:
    return {
        "old_index": 0 if old_content else None,
        "new_index": 0 if new_content else None,
        "similarity": similarity,
        "old_title": old_title,
        "new_title": new_title,
        "old_content": old_content,
        "new_content": new_content,
    }
