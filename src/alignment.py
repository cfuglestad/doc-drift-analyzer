import difflib
from typing import List, Dict


def similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def align_sections(old_sections: List[Dict[str, str]], new_sections: List[Dict[str, str]], threshold: float = 0.35):
    aligned = []
    used_new = set()

    for i, old_sec in enumerate(old_sections):
        best_j = None
        best_score = -1.0

        for j, new_sec in enumerate(new_sections):
            if j in used_new:
                continue

            title_score = similarity(old_sec["title"], new_sec["title"])
            body_score = similarity(old_sec["content"], new_sec["content"])
            score = 0.4 * title_score + 0.6 * body_score

            if score > best_score:
                best_score = score
                best_j = j

        if best_j is not None and best_score >= threshold:
            used_new.add(best_j)
            aligned.append({
                "old_index": i,
                "new_index": best_j,
                "similarity": best_score,
                "old_title": old_sec["title"],
                "new_title": new_sections[best_j]["title"],
                "old_content": old_sec["content"],
                "new_content": new_sections[best_j]["content"],
            })
        else:
            aligned.append({
                "old_index": i,
                "new_index": None,
                "similarity": 0.0,
                "old_title": old_sec["title"],
                "new_title": "",
                "old_content": old_sec["content"],
                "new_content": "",
            })

    for j, new_sec in enumerate(new_sections):
        if j not in used_new:
            aligned.append({
                "old_index": None,
                "new_index": j,
                "similarity": 0.0,
                "old_title": "",
                "new_title": new_sec["title"],
                "old_content": "",
                "new_content": new_sec["content"],
            })

    return aligned
