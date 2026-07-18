"""Tests for explicit backend selection and fallback behavior."""

from collections.abc import Sequence

import pytest

from src.config import (
    AlignmentConfig,
    FallbackReason,
    SimilarityBackendType,
    build_backend,
    recommended_threshold,
)
from src.semantic import (
    SemanticDependencyUnavailableError,
    SemanticModelInitializationError,
)
from src.similarity import HybridSimilarityBackend, LexicalSimilarityBackend


class FixedEncoder:
    """Return the same normalized embedding for every input."""

    def encode(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        return tuple((1.0, 0.0) for _ in texts)


class FixedBackend:
    """Return one controlled score."""

    def __init__(self, value: float) -> None:
        self.value = value

    def score(self, first: str, second: str) -> float:
        return self.value


def test_lexical_backend_selection_preserves_default_threshold() -> None:
    selection = build_backend(AlignmentConfig())

    assert isinstance(selection.backend, LexicalSimilarityBackend)
    assert selection.active_backend is SimilarityBackendType.LEXICAL
    assert selection.threshold == 0.35
    assert selection.fallback is None


def test_semantic_backend_selection_uses_backend_specific_threshold() -> None:
    selection = build_backend(
        AlignmentConfig(backend=SimilarityBackendType.SEMANTIC),
        semantic_encoder_factory=lambda _: FixedEncoder(),
    )

    assert selection.active_backend is SimilarityBackendType.SEMANTIC
    assert selection.threshold == recommended_threshold(SimilarityBackendType.SEMANTIC)
    assert selection.backend.score("first", "second") == 1.0


def test_explicit_threshold_overrides_backend_recommendation() -> None:
    selection = build_backend(
        AlignmentConfig(backend=SimilarityBackendType.SEMANTIC, threshold=0.82),
        semantic_encoder_factory=lambda _: FixedEncoder(),
    )

    assert selection.threshold == 0.82


def test_fallback_enabled_returns_structured_metadata() -> None:
    def unavailable_encoder(_: str) -> FixedEncoder:
        raise SemanticDependencyUnavailableError("dependency missing")

    selection = build_backend(
        AlignmentConfig(backend=SimilarityBackendType.SEMANTIC, fallback_to_lexical=True),
        semantic_encoder_factory=unavailable_encoder,
    )

    assert isinstance(selection.backend, LexicalSimilarityBackend)
    assert selection.active_backend is SimilarityBackendType.LEXICAL
    assert selection.fallback is not None
    assert selection.fallback.reason is FallbackReason.DEPENDENCY_UNAVAILABLE
    assert selection.fallback.requested_backend is SimilarityBackendType.SEMANTIC
    assert selection.fallback.message == "dependency missing"


def test_fallback_disabled_exposes_initialization_failure() -> None:
    def unavailable_encoder(_: str) -> FixedEncoder:
        raise SemanticDependencyUnavailableError("dependency missing")

    with pytest.raises(SemanticDependencyUnavailableError, match="dependency missing"):
        build_backend(
            AlignmentConfig(
                backend=SimilarityBackendType.SEMANTIC,
                fallback_to_lexical=False,
            ),
            semantic_encoder_factory=unavailable_encoder,
        )


def test_model_initialization_fallback_is_structured() -> None:
    def broken_model(_: str) -> FixedEncoder:
        raise SemanticModelInitializationError("model unavailable")

    selection = build_backend(
        AlignmentConfig(backend=SimilarityBackendType.HYBRID),
        semantic_encoder_factory=broken_model,
    )

    assert selection.fallback is not None
    assert selection.fallback.reason is FallbackReason.MODEL_INITIALIZATION_FAILED
    assert selection.fallback.message == "model unavailable"


def test_hybrid_backend_calculates_explicit_weighted_score() -> None:
    backend = HybridSimilarityBackend(
        lexical_backend=FixedBackend(0.2),
        semantic_backend=FixedBackend(0.8),
        lexical_weight=0.25,
        semantic_weight=0.75,
    )

    assert backend.score("first", "second") == pytest.approx(0.65)


@pytest.mark.parametrize(
    ("lexical_weight", "semantic_weight"),
    [(-0.1, 1.1), (0.4, 0.4), (float("inf"), 0.0)],
)
def test_hybrid_backend_rejects_invalid_weights(
    lexical_weight: float, semantic_weight: float
) -> None:
    with pytest.raises(ValueError, match="weights"):
        HybridSimilarityBackend(
            lexical_backend=FixedBackend(0.2),
            semantic_backend=FixedBackend(0.8),
            lexical_weight=lexical_weight,
            semantic_weight=semantic_weight,
        )


def test_alignment_config_rejects_invalid_threshold() -> None:
    with pytest.raises(ValueError, match="threshold"):
        AlignmentConfig(threshold=1.1)


def test_alignment_config_rejects_invalid_hybrid_weights_before_model_loading() -> None:
    with pytest.raises(ValueError, match="sum"):
        AlignmentConfig(
            backend=SimilarityBackendType.HYBRID,
            lexical_weight=0.2,
            semantic_weight=0.2,
        )
