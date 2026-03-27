import difflib
from typing import Dict, List


def classify_change(old_text: str, new_text: str, similarity_score: float) -> str:
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
    old_words = old_text.split()
    new_words = new_text.split()

    matcher = difflib.SequenceMatcher(None, old_words, new_words)
    html_parts = []

    for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
        if opcode == "equal":
            html_parts.append(" ".join(new_words[j1:j2]))
        elif opcode == "insert":
            inserted = " ".join(new_words[j1:j2])
            html_parts.append(
                f"<span style='background-color:#d1fae5;padding:2px 4px;border-radius:4px;'>{inserted}</span>"
            )
        elif opcode == "delete":
            deleted = " ".join(old_words[i1:i2])
            html_parts.append(
                f"<span style='background-color:#fee2e2;padding:2px 4px;border-radius:4px;text-decoration:line-through;'>{deleted}</span>"
            )
        elif opcode == "replace":
            deleted = " ".join(old_words[i1:i2])
            inserted = " ".join(new_words[j1:j2])
            html_parts.append(
                f"<span style='background-color:#fee2e2;padding:2px 4px;border-radius:4px;text-decoration:line-through;'>{deleted}</span> "
                f"<span style='background-color:#d1fae5;padding:2px 4px;border-radius:4px;'>{inserted}</span>"
            )

    return " ".join(html_parts)


def summarize_changes(aligned_rows: List[Dict]) -> Dict[str, int]:
    summary = {
        "Added": 0,
        "Removed": 0,
        "Edited (minor)": 0,
        "Edited (major)": 0,
        "Unchanged": 0,
    }

    for row in aligned_rows:
        label = classify_change(row["old_content"], row["new_content"], row["similarity"])
        summary[label] += 1

    return summary
