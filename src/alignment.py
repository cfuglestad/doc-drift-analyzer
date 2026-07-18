"""Section alignment services and compatibility APIs."""

from collections.abc import Sequence

from src.models import (
    AlignmentResult,
    AlignmentRow,
    Section,
    SectionInput,
    alignment_to_row,
    coerce_section,
)
from src.similarity import LexicalSimilarityBackend, SimilarityBackend


class SectionAligner:
    """Greedily align sections using an injected similarity backend."""

    def __init__(self, similarity_backend: SimilarityBackend) -> None:
        """Initialize the aligner.

        Args:
            similarity_backend: Backend used only to score pairs of text.
        """
        self._similarity_backend = similarity_backend

    def align(
        self,
        old_sections: Sequence[Section],
        new_sections: Sequence[Section],
        threshold: float = 0.35,
    ) -> list[AlignmentResult]:
        """Align old document sections with their closest new sections.

        Args:
            old_sections: Sections extracted from the old document.
            new_sections: Sections extracted from the new document.
            threshold: Minimum weighted similarity needed for an alignment.

        Returns:
            Typed results containing matched, removed, and added sections.
        """
        aligned: list[AlignmentResult] = []
        used_new: set[int] = set()

        for old_index, old_section in enumerate(old_sections):
            best_new_index: int | None = None
            best_score = -1.0

            for new_index, new_section in enumerate(new_sections):
                if new_index in used_new:
                    continue

                title_score = self._similarity_backend.score(old_section.title, new_section.title)
                body_score = self._similarity_backend.score(
                    old_section.content, new_section.content
                )
                score = 0.4 * title_score + 0.6 * body_score

                if score > best_score:
                    best_score = score
                    best_new_index = new_index

            if best_new_index is not None and best_score >= threshold:
                used_new.add(best_new_index)
                aligned.append(
                    AlignmentResult(
                        old_section=old_section,
                        new_section=new_sections[best_new_index],
                        similarity=best_score,
                        old_index=old_index,
                        new_index=best_new_index,
                    )
                )
            else:
                aligned.append(
                    AlignmentResult(
                        old_section=old_section,
                        new_section=None,
                        similarity=0.0,
                        old_index=old_index,
                        new_index=None,
                    )
                )

        for new_index, new_section in enumerate(new_sections):
            if new_index not in used_new:
                aligned.append(
                    AlignmentResult(
                        old_section=None,
                        new_section=new_section,
                        similarity=0.0,
                        old_index=None,
                        new_index=new_index,
                    )
                )

        return aligned


def similarity(first: str, second: str) -> float:
    """Return lexical similarity through the default backend compatibility API."""
    return LexicalSimilarityBackend().score(first, second)


def align_sections(
    old_sections: Sequence[SectionInput],
    new_sections: Sequence[SectionInput],
    threshold: float = 0.35,
) -> list[AlignmentRow]:
    """Return legacy alignment dictionaries using the default alignment service."""
    aligner = SectionAligner(similarity_backend=LexicalSimilarityBackend())
    results = aligner.align(
        [coerce_section(section) for section in old_sections],
        [coerce_section(section) for section in new_sections],
        threshold,
    )
    return [alignment_to_row(result) for result in results]
