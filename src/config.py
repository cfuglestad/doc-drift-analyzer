"""Explicit similarity backend configuration and construction."""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from src.semantic import (
    SemanticBackendError,
    SemanticDependencyUnavailableError,
    SemanticEncoder,
    SemanticSimilarityBackend,
    SentenceTransformerEncoder,
)
from src.similarity import (
    HybridSimilarityBackend,
    LexicalSimilarityBackend,
    SimilarityBackend,
    validate_hybrid_weights,
)

LOGGER = logging.getLogger(__name__)
DEFAULT_SEMANTIC_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class SimilarityBackendType(StrEnum):
    """Supported, explicitly constructed similarity backends."""

    LEXICAL = "lexical"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class FallbackReason(StrEnum):
    """Structured reason for selecting lexical fallback."""

    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"
    MODEL_INITIALIZATION_FAILED = "model_initialization_failed"


def recommended_threshold(backend: SimilarityBackendType) -> float:
    """Return the evaluated default threshold for a backend."""
    return {
        SimilarityBackendType.LEXICAL: 0.35,
        SimilarityBackendType.SEMANTIC: 0.65,
        SimilarityBackendType.HYBRID: 0.50,
    }[backend]


@dataclass(frozen=True, slots=True)
class AlignmentConfig:
    """Typed configuration for backend construction and alignment thresholding."""

    backend: SimilarityBackendType = SimilarityBackendType.LEXICAL
    threshold: float | None = None
    fallback_to_lexical: bool = True
    model_identifier: str = DEFAULT_SEMANTIC_MODEL
    lexical_weight: float = 0.5
    semantic_weight: float = 0.5

    def __post_init__(self) -> None:
        if self.threshold is not None and not 0.0 <= self.threshold <= 1.0:
            raise ValueError("Alignment threshold must be between 0.0 and 1.0.")
        if self.backend is SimilarityBackendType.HYBRID:
            validate_hybrid_weights(self.lexical_weight, self.semantic_weight)

    @property
    def effective_threshold(self) -> float:
        """Return an explicit threshold or the backend-specific recommendation."""
        return self.threshold if self.threshold is not None else recommended_threshold(self.backend)


@dataclass(frozen=True, slots=True)
class FallbackMetadata:
    """Observable details about a requested backend falling back to lexical."""

    requested_backend: SimilarityBackendType
    active_backend: SimilarityBackendType
    reason: FallbackReason
    message: str


@dataclass(frozen=True, slots=True)
class BackendSelection:
    """Constructed backend plus active configuration and fallback state."""

    backend: SimilarityBackend
    requested_backend: SimilarityBackendType
    active_backend: SimilarityBackendType
    threshold: float
    fallback: FallbackMetadata | None = None


SemanticEncoderFactory = Callable[[str], SemanticEncoder]


def build_backend(
    config: AlignmentConfig,
    semantic_encoder_factory: SemanticEncoderFactory = SentenceTransformerEncoder,
) -> BackendSelection:
    """Construct one configured backend with explicit lexical fallback behavior."""
    if config.backend is SimilarityBackendType.LEXICAL:
        return BackendSelection(
            backend=LexicalSimilarityBackend(),
            requested_backend=config.backend,
            active_backend=config.backend,
            threshold=config.effective_threshold,
        )

    try:
        semantic_backend = SemanticSimilarityBackend(
            encoder=semantic_encoder_factory(config.model_identifier)
        )
        backend: SimilarityBackend = semantic_backend
        if config.backend is SimilarityBackendType.HYBRID:
            backend = HybridSimilarityBackend(
                lexical_backend=LexicalSimilarityBackend(),
                semantic_backend=semantic_backend,
                lexical_weight=config.lexical_weight,
                semantic_weight=config.semantic_weight,
            )
        return BackendSelection(
            backend=backend,
            requested_backend=config.backend,
            active_backend=config.backend,
            threshold=config.effective_threshold,
        )
    except SemanticBackendError as error:
        if not config.fallback_to_lexical:
            raise
        reason = (
            FallbackReason.DEPENDENCY_UNAVAILABLE
            if isinstance(error, SemanticDependencyUnavailableError)
            else FallbackReason.MODEL_INITIALIZATION_FAILED
        )
        LOGGER.warning(
            "Similarity backend %s unavailable; using lexical fallback: %s",
            config.backend.value,
            error,
        )
        fallback = FallbackMetadata(
            requested_backend=config.backend,
            active_backend=SimilarityBackendType.LEXICAL,
            reason=reason,
            message=str(error),
        )
        return BackendSelection(
            backend=LexicalSimilarityBackend(),
            requested_backend=config.backend,
            active_backend=SimilarityBackendType.LEXICAL,
            threshold=recommended_threshold(SimilarityBackendType.LEXICAL),
            fallback=fallback,
        )
