"""Tests for change classification and inline diffs."""

import pytest

from src.diffing import classify_change, summarize_changes, word_diff_html
from src.models import AlignmentRow


@pytest.mark.parametrize(
    ("old_text", "new_text", "score", "expected"),
    [
        ("removed", "", 0.0, "Removed"),
        ("", "added", 0.0, "Added"),
        ("same", "same", 0.99, "Unchanged"),
        ("old", "new", 0.80, "Edited (minor)"),
        ("old", "new", 0.75, "Edited (major)"),
    ],
)
def test_classify_change(old_text: str, new_text: str, score: float, expected: str) -> None:
    assert classify_change(old_text, new_text, score) == expected


def test_word_diff_html_preserves_equal_words() -> None:
    assert word_diff_html("one two", "one two") == "one two"


def test_word_diff_html_highlights_insertions() -> None:
    result = word_diff_html("one", "one two")

    assert "one" in result
    assert "background-color:#d1fae5" in result
    assert ">two</span>" in result


def test_word_diff_html_highlights_deletions() -> None:
    result = word_diff_html("one two", "one")

    assert "background-color:#fee2e2" in result
    assert "text-decoration:line-through" in result
    assert ">two</span>" in result


def test_word_diff_html_highlights_replacements() -> None:
    result = word_diff_html("old value", "new value")

    assert ">old</span>" in result
    assert ">new</span>" in result
    assert result.count("background-color:") == 2


def test_summarize_changes_counts_every_classification() -> None:
    rows: list[AlignmentRow] = [
        _row("", "added", 0.0),
        _row("removed", "", 0.0),
        _row("old", "new", 0.8),
        _row("old", "new", 0.5),
        _row("same", "same", 1.0),
    ]

    assert summarize_changes(rows) == {
        "Added": 1,
        "Removed": 1,
        "Edited (minor)": 1,
        "Edited (major)": 1,
        "Unchanged": 1,
    }


def _row(old_content: str, new_content: str, similarity: float) -> AlignmentRow:
    return {
        "old_index": 0 if old_content else None,
        "new_index": 0 if new_content else None,
        "similarity": similarity,
        "old_title": "Old" if old_content else "",
        "new_title": "New" if new_content else "",
        "old_content": old_content,
        "new_content": new_content,
    }
