"""Rule-based extraction of sections from plain text."""

import re

from src.models import Section


def extract_sections(text: str) -> list[Section]:
    """Extract titled sections using all-caps and numbered headings.

    Text before the first heading is assigned to an ``Introduction`` section.
    When no headings are present, the non-empty input becomes one section.
    """
    lines = text.splitlines()
    sections: list[Section] = []
    current_title = "Introduction"
    current_body: list[str] = []

    heading_pattern = re.compile(r"^([A-Z][A-Z0-9 /&()\-]{3,}|(\d+(\.\d+)*\s+.+))$")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            current_body.append("")
            continue

        if heading_pattern.match(stripped):
            if current_body:
                sections.append(
                    Section(title=current_title, content="\n".join(current_body).strip())
                )
            current_title = stripped
            current_body = []
        else:
            current_body.append(stripped)

    if current_body:
        sections.append(Section(title=current_title, content="\n".join(current_body).strip()))

    return [section for section in sections if section.content]
