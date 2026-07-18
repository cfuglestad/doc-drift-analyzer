"""Tests for the injected section alignment service."""

import pytest

from src.alignment import SectionAligner
from src.models import Section
from src.similarity import SimilarityBackend


class FixedSimilarityBackend:
    """Return one deterministic value for every comparison."""

    def __init__(self, value: float) -> None:
        self.value = value
        self.calls: list[tuple[str, str]] = []

    def score(self, first: str, second: str) -> float:
        self.calls.append((first, second))
        return self.value


class MappingSimilarityBackend:
    """Return scores selected by the exact input pair."""

    def __init__(self, scores: dict[tuple[str, str], float]) -> None:
        self.scores = scores

    def score(self, first: str, second: str) -> float:
        return self.scores.get((first, second), 0.0)


def test_section_aligner_uses_injected_backend_and_retains_score() -> None:
    backend = FixedSimilarityBackend(0.8)
    protocol_backend: SimilarityBackend = backend
    aligner = SectionAligner(similarity_backend=protocol_backend)

    results = aligner.align(
        [Section(title="Old title", content="Old body")],
        [Section(title="New title", content="New body")],
    )

    assert backend.calls == [("Old title", "New title"), ("Old body", "New body")]
    assert len(results) == 1
    assert results[0].similarity == pytest.approx(0.8)
    assert results[0].old_section == Section(title="Old title", content="Old body")
    assert results[0].new_section == Section(title="New title", content="New body")


def test_section_aligner_threshold_controls_match() -> None:
    aligner = SectionAligner(similarity_backend=FixedSimilarityBackend(0.34))

    results = aligner.align(
        [Section(title="Old", content="Old")],
        [Section(title="New", content="New")],
        threshold=0.35,
    )

    assert len(results) == 2
    assert results[0].old_section is not None
    assert results[0].new_section is None
    assert results[1].old_section is None
    assert results[1].new_section is not None


def test_fake_backend_controls_which_section_is_aligned() -> None:
    backend = MappingSimilarityBackend(
        {
            ("Old title", "Best title"): 1.0,
            ("Old body", "Best body"): 1.0,
        }
    )
    aligner = SectionAligner(similarity_backend=backend)

    results = aligner.align(
        [Section(title="Old title", content="Old body")],
        [
            Section(title="Other title", content="Other body"),
            Section(title="Best title", content="Best body"),
        ],
    )

    assert results[0].new_index == 1
    assert results[0].similarity == 1.0
    assert results[1].old_section is None
    assert results[1].new_index == 0


def test_section_aligner_identifies_added_section() -> None:
    aligner = SectionAligner(similarity_backend=FixedSimilarityBackend(1.0))
    added = Section(title="Added", content="New content")

    results = aligner.align([], [added])

    assert results[0].old_section is None
    assert results[0].new_section is added
    assert results[0].new_index == 0


def test_section_aligner_identifies_removed_section() -> None:
    aligner = SectionAligner(similarity_backend=FixedSimilarityBackend(1.0))
    removed = Section(title="Removed", content="Old content")

    results = aligner.align([removed], [])

    assert results[0].old_section is removed
    assert results[0].new_section is None
    assert results[0].old_index == 0
