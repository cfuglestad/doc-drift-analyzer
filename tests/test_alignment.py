"""Tests for lexical section alignment."""

import pytest

from src.alignment import align_sections, similarity
from src.models import Section


def test_similarity_identical_and_different_text() -> None:
    assert similarity("same", "same") == 1.0
    assert similarity("abc", "xyz") == 0.0


def test_align_sections_matches_best_section_and_marks_addition() -> None:
    old_sections: list[Section] = [{"title": "Policy", "content": "Keep records."}]
    new_sections: list[Section] = [
        {"title": "Appendix", "content": "Reference material."},
        {"title": "Policy", "content": "Keep records."},
    ]

    aligned = align_sections(old_sections, new_sections)

    assert aligned[0] == {
        "old_index": 0,
        "new_index": 1,
        "similarity": pytest.approx(1.0),
        "old_title": "Policy",
        "new_title": "Policy",
        "old_content": "Keep records.",
        "new_content": "Keep records.",
    }
    assert aligned[1]["old_index"] is None
    assert aligned[1]["new_index"] == 0
    assert aligned[1]["new_title"] == "Appendix"


def test_align_sections_marks_below_threshold_sections_removed_and_added() -> None:
    old_sections: list[Section] = [{"title": "Old", "content": "Legacy content"}]
    new_sections: list[Section] = [{"title": "New", "content": "Replacement"}]

    aligned = align_sections(old_sections, new_sections, threshold=1.1)

    assert len(aligned) == 2
    assert aligned[0]["new_index"] is None
    assert aligned[0]["old_content"] == "Legacy content"
    assert aligned[1]["old_index"] is None
    assert aligned[1]["new_content"] == "Replacement"


def test_align_sections_does_not_reuse_a_new_section() -> None:
    old_sections: list[Section] = [
        {"title": "Policy", "content": "Same content"},
        {"title": "Policy", "content": "Same content"},
    ]
    new_sections: list[Section] = [{"title": "Policy", "content": "Same content"}]

    aligned = align_sections(old_sections, new_sections)

    assert aligned[0]["new_index"] == 0
    assert aligned[1]["new_index"] is None


def test_align_sections_handles_empty_inputs() -> None:
    assert align_sections([], []) == []
