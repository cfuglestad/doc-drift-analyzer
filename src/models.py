"""Typed domain models and compatibility boundary types."""

from dataclasses import dataclass
from typing import Literal, TypedDict

ChangeLabel = Literal[
    "Added",
    "Removed",
    "Edited (minor)",
    "Edited (major)",
    "Unchanged",
]


@dataclass(frozen=True, slots=True)
class Section:
    """A titled block of document content."""

    title: str
    content: str


@dataclass(frozen=True, slots=True)
class AlignmentResult:
    """A possible correspondence between an old and a new section."""

    old_section: Section | None
    new_section: Section | None
    similarity: float
    old_index: int | None
    new_index: int | None

    @property
    def old_title(self) -> str:
        """Return the old title or an empty compatibility value."""
        return self.old_section.title if self.old_section is not None else ""

    @property
    def new_title(self) -> str:
        """Return the new title or an empty compatibility value."""
        return self.new_section.title if self.new_section is not None else ""

    @property
    def old_content(self) -> str:
        """Return the old content or an empty compatibility value."""
        return self.old_section.content if self.old_section is not None else ""

    @property
    def new_content(self) -> str:
        """Return the new content or an empty compatibility value."""
        return self.new_section.content if self.new_section is not None else ""


@dataclass(frozen=True, slots=True)
class ChangeSummary:
    """Aggregate change counts and deterministic summary bullets."""

    added: int
    removed: int
    minor_edits: int
    major_edits: int
    unchanged: int
    bullets: tuple[str, ...] = ()

    def as_counts(self) -> dict[ChangeLabel, int]:
        """Return counts using the application's established labels."""
        return {
            "Added": self.added,
            "Removed": self.removed,
            "Edited (minor)": self.minor_edits,
            "Edited (major)": self.major_edits,
            "Unchanged": self.unchanged,
        }


class SectionData(TypedDict):
    """Legacy dictionary representation accepted at compatibility boundaries."""

    title: str
    content: str


class AlignmentRow(TypedDict):
    """Legacy alignment dictionary returned by compatibility functions."""

    old_index: int | None
    new_index: int | None
    similarity: float
    old_title: str
    new_title: str
    old_content: str
    new_content: str


SectionInput = Section | SectionData
AlignmentInput = AlignmentResult | AlignmentRow


def coerce_section(section: SectionInput) -> Section:
    """Convert a legacy section dictionary to the domain model when needed."""
    if isinstance(section, Section):
        return section
    return Section(title=section["title"], content=section["content"])


def coerce_alignment(alignment: AlignmentInput) -> AlignmentResult:
    """Convert a legacy alignment dictionary to the domain model when needed."""
    if isinstance(alignment, AlignmentResult):
        return alignment

    old_section = (
        Section(title=alignment["old_title"], content=alignment["old_content"])
        if alignment["old_index"] is not None
        else None
    )
    new_section = (
        Section(title=alignment["new_title"], content=alignment["new_content"])
        if alignment["new_index"] is not None
        else None
    )
    return AlignmentResult(
        old_section=old_section,
        new_section=new_section,
        similarity=alignment["similarity"],
        old_index=alignment["old_index"],
        new_index=alignment["new_index"],
    )


def alignment_to_row(alignment: AlignmentResult) -> AlignmentRow:
    """Convert a domain alignment to its legacy dictionary representation."""
    return {
        "old_index": alignment.old_index,
        "new_index": alignment.new_index,
        "similarity": alignment.similarity,
        "old_title": alignment.old_title,
        "new_title": alignment.new_title,
        "old_content": alignment.old_content,
        "new_content": alignment.new_content,
    }
