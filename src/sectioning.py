import re
from typing import List, Dict


def extract_sections(text: str) -> List[Dict[str, str]]:
    """
    Lightweight section extractor.
    Tries to split on all-caps headings or numbered headings.
    Falls back to paragraph chunks if no headings found.
    """
    lines = text.splitlines()
    sections = []
    current_title = "Introduction"
    current_body = []

    heading_pattern = re.compile(r"^([A-Z][A-Z0-9 /&()\-]{3,}|(\d+(\.\d+)*\s+.+))$")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            current_body.append("")
            continue

        if heading_pattern.match(stripped):
            if current_body:
                sections.append({
                    "title": current_title,
                    "content": "\n".join(current_body).strip()
                })
            current_title = stripped
            current_body = []
        else:
            current_body.append(stripped)

    if current_body:
        sections.append({
            "title": current_title,
            "content": "\n".join(current_body).strip()
        })

    return [s for s in sections if s["content"]]
