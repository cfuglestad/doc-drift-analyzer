"""Human-readable summaries of document changes."""

from src.diffing import classify_change
from src.models import AlignmentRow


def build_change_bullets(aligned_rows: list[AlignmentRow]) -> list[str]:
    """Build concise bullet text for all changed alignment rows."""
    bullets: list[str] = []

    for row in aligned_rows:
        label = classify_change(row["old_content"], row["new_content"], row["similarity"])

        if label == "Unchanged":
            continue

        old_title = row["old_title"] or "Untitled"
        new_title = row["new_title"] or "Untitled"

        if label == "Added":
            bullets.append(f"Added section: {new_title}")
        elif label == "Removed":
            bullets.append(f"Removed section: {old_title}")
        elif label == "Edited (minor)":
            bullets.append(f"Minor edits in section: {old_title}")
        elif label == "Edited (major)":
            bullets.append(f"Major edits in section: {old_title} -> {new_title}")

    return bullets
