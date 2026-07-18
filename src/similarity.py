"""Similarity interfaces and default implementations."""

import difflib
import math
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


class HybridSimilarityBackend:
    """Combine lexical and semantic scores with explicit fixed weights."""

    def __init__(
        self,
        lexical_backend: SimilarityBackend,
        semantic_backend: SimilarityBackend,
        lexical_weight: float = 0.5,
        semantic_weight: float = 0.5,
    ) -> None:
        """Initialize a transparent weighted combination.

        Args:
            lexical_backend: Backend contributing the lexical score.
            semantic_backend: Backend contributing the semantic score.
            lexical_weight: Non-negative lexical contribution.
            semantic_weight: Non-negative semantic contribution.

        Raises:
            ValueError: If weights are invalid or do not sum to one.
        """
        validate_hybrid_weights(lexical_weight, semantic_weight)
        self._lexical_backend = lexical_backend
        self._semantic_backend = semantic_backend
        self._lexical_weight = lexical_weight
        self._semantic_weight = semantic_weight

    def score(self, first: str, second: str) -> float:
        """Return the configured weighted mean of normalized backend scores."""
        return self._lexical_weight * self._lexical_backend.score(
            first, second
        ) + self._semantic_weight * self._semantic_backend.score(first, second)


def validate_hybrid_weights(lexical_weight: float, semantic_weight: float) -> None:
    """Validate transparent hybrid weights without constructing a backend."""
    weights = (lexical_weight, semantic_weight)
    if any(not math.isfinite(weight) or weight < 0.0 for weight in weights):
        raise ValueError("Hybrid weights must be finite and non-negative.")
    if not math.isclose(sum(weights), 1.0, abs_tol=1e-9):
        raise ValueError("Hybrid weights must sum to 1.0.")
