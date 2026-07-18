"""Tests for the default change summarization service."""

from src.models import AlignmentResult, ChangeSummary, Section
from src.summarization import ChangeSummarizer, RuleBasedChangeSummarizer


def test_rule_based_summarizer_preserves_counts_and_wording() -> None:
    summarizer: ChangeSummarizer = RuleBasedChangeSummarizer()
    alignments = [
        _alignment(None, Section("New", "added"), 0.0),
        _alignment(Section("Old", "removed"), None, 0.0),
        _alignment(Section("Policy", "old"), Section("Policy", "new"), 0.8),
        _alignment(Section("Scope", "old"), Section("Coverage", "new"), 0.5),
        _alignment(Section("Same", "same"), Section("Same", "same"), 1.0),
    ]

    assert summarizer.summarize(alignments) == ChangeSummary(
        added=1,
        removed=1,
        minor_edits=1,
        major_edits=1,
        unchanged=1,
        bullets=(
            "Added section: New",
            "Removed section: Old",
            "Minor edits in section: Policy",
            "Major edits in section: Scope -> Coverage",
        ),
    )


def _alignment(
    old_section: Section | None,
    new_section: Section | None,
    similarity: float,
) -> AlignmentResult:
    return AlignmentResult(
        old_section=old_section,
        new_section=new_section,
        similarity=similarity,
        old_index=0 if old_section is not None else None,
        new_index=0 if new_section is not None else None,
    )
