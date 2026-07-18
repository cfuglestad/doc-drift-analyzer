"""Change summarization interfaces, services, and compatibility APIs."""

from collections.abc import Sequence
from typing import Protocol

from src.diffing import classify_change
from src.models import AlignmentInput, AlignmentResult, ChangeSummary, coerce_alignment


class ChangeSummarizer(Protocol):
    """Create a typed summary from aligned document sections."""

    def summarize(self, alignments: Sequence[AlignmentResult]) -> ChangeSummary:
        """Return aggregate counts and human-readable summary bullets."""
        ...


class RuleBasedChangeSummarizer:
    """Preserve the project's deterministic change-summary behavior."""

    def summarize(self, alignments: Sequence[AlignmentResult]) -> ChangeSummary:
        """Summarize alignments using established labels and wording."""
        added = 0
        removed = 0
        minor_edits = 0
        major_edits = 0
        unchanged = 0
        bullets: list[str] = []

        for alignment in alignments:
            label = classify_change(
                alignment.old_content,
                alignment.new_content,
                alignment.similarity,
            )

            if label == "Added":
                added += 1
                bullets.append(f"Added section: {alignment.new_title or 'Untitled'}")
            elif label == "Removed":
                removed += 1
                bullets.append(f"Removed section: {alignment.old_title or 'Untitled'}")
            elif label == "Edited (minor)":
                minor_edits += 1
                bullets.append(f"Minor edits in section: {alignment.old_title or 'Untitled'}")
            elif label == "Edited (major)":
                major_edits += 1
                bullets.append(
                    "Major edits in section: "
                    f"{alignment.old_title or 'Untitled'} -> "
                    f"{alignment.new_title or 'Untitled'}"
                )
            else:
                unchanged += 1

        return ChangeSummary(
            added=added,
            removed=removed,
            minor_edits=minor_edits,
            major_edits=major_edits,
            unchanged=unchanged,
            bullets=tuple(bullets),
        )


def build_change_bullets(aligned_rows: Sequence[AlignmentInput]) -> list[str]:
    """Return legacy bullet output through the default summarizer service."""
    alignments = [coerce_alignment(row) for row in aligned_rows]
    return list(RuleBasedChangeSummarizer().summarize(alignments).bullets)
