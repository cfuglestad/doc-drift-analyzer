"""Similarity interfaces and default implementations."""

import difflib
from typing import Protocol


class SimilarityBackend(Protocol):
    """Compute a normalized similarity score for two text inputs."""

    def score(self, first: str, second: str) -> float:
        """Return a similarity score, preferably between zero and one."""
        ...


class LexicalSimilarityBackend:
    """Calculate similarity with the project's original lexical algorithm."""

    def score(self, first: str, second: str) -> float:
        """Return the ``difflib.SequenceMatcher`` similarity ratio."""
        return difflib.SequenceMatcher(None, first, second).ratio()
