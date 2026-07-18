"""Change classification and inline diff utilities."""

import difflib
from collections.abc import Sequence

from src.models import AlignmentInput, ChangeLabel, coerce_alignment

_INSERTED_STYLE = "background-color:#d1fae5;padding:2px 4px;border-radius:4px;"
_DELETED_STYLE = (
    "background-color:#fee2e2;padding:2px 4px;border-radius:4px;" "text-decoration:line-through;"
)


def classify_change(old_text: str, new_text: str, similarity_score: float) -> ChangeLabel:
    """Classify an aligned section as added, removed, edited, or unchanged."""
    if old_text and not new_text:
        return "Removed"
    if new_text and not old_text:
        return "Added"
    if similarity_score > 0.98:
        return "Unchanged"
    if similarity_score > 0.75:
        return "Edited (minor)"
    return "Edited (major)"


def word_diff_html(old_text: str, new_text: str) -> str:
    """Render word-level insertions and deletions as styled HTML."""
    old_words = old_text.split()
    new_words = new_text.split()

    matcher = difflib.SequenceMatcher(None, old_words, new_words)
    html_parts: list[str] = []

    for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
        if opcode == "equal":
            html_parts.append(" ".join(new_words[j1:j2]))
        elif opcode == "insert":
            inserted = " ".join(new_words[j1:j2])
            html_parts.append(f"<span style='{_INSERTED_STYLE}'>{inserted}</span>")
        elif opcode == "delete":
            deleted = " ".join(old_words[i1:i2])
            html_parts.append(f"<span style='{_DELETED_STYLE}'>{deleted}</span>")
        elif opcode == "replace":
            deleted = " ".join(old_words[i1:i2])
            inserted = " ".join(new_words[j1:j2])
            html_parts.append(
                f"<span style='{_DELETED_STYLE}'>{deleted}</span> "
                f"<span style='{_INSERTED_STYLE}'>{inserted}</span>"
            )

    return " ".join(html_parts)


def summarize_changes(aligned_rows: Sequence[AlignmentInput]) -> dict[ChangeLabel, int]:
    """Return legacy count output through the default summarizer service."""
    from src.summarization import RuleBasedChangeSummarizer

    alignments = [coerce_alignment(row) for row in aligned_rows]
    return RuleBasedChangeSummarizer().summarize(alignments).as_counts()
