"""Tests for legacy functions at typed and dictionary boundaries."""

from src.alignment import align_sections
from src.diffing import summarize_changes
from src.models import AlignmentResult, Section
from src.summarization import build_change_bullets


def test_alignment_wrapper_accepts_domain_sections_and_returns_rows() -> None:
    rows = align_sections(
        [Section(title="Policy", content="Same")],
        [Section(title="Policy", content="Same")],
    )

    assert rows == [
        {
            "old_index": 0,
            "new_index": 0,
            "similarity": 1.0,
            "old_title": "Policy",
            "new_title": "Policy",
            "old_content": "Same",
            "new_content": "Same",
        }
    ]


def test_summary_wrappers_accept_domain_alignments() -> None:
    alignment = AlignmentResult(
        old_section=None,
        new_section=Section(title="New", content="Added content"),
        similarity=0.0,
        old_index=None,
        new_index=0,
    )

    assert summarize_changes([alignment]) == {
        "Added": 1,
        "Removed": 0,
        "Edited (minor)": 0,
        "Edited (major)": 0,
        "Unchanged": 0,
    }
    assert build_change_bullets([alignment]) == ["Added section: New"]
