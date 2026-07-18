"""Optional local sentence-embedding similarity implementation."""

import math
from collections.abc import Callable, Iterable, Sequence
from importlib import import_module
from types import ModuleType
from typing import Protocol, cast


class SemanticBackendError(RuntimeError):
    """Base error for semantic backend initialization or scoring failures."""


class SemanticDependencyUnavailableError(SemanticBackendError):
    """Raised when the optional sentence-transformers dependency is absent."""


class SemanticModelInitializationError(SemanticBackendError):
    """Raised when a configured local embedding model cannot be initialized."""


class SemanticEncoder(Protocol):
    """Encode text into unit-normalized vectors."""

    def encode(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        """Return one unit-normalized vector per input text."""
        ...


class _SentenceTransformerModel(Protocol):
    def __init__(self, model_name_or_path: str) -> None:
        """Initialize a model from a local path or model identifier."""
        ...

    def encode(self, sentences: list[str], *, normalize_embeddings: bool) -> object:
        """Return model embeddings."""
        ...


ModuleLoader = Callable[[str], ModuleType]


class SentenceTransformerEncoder:
    """Adapter around an optional, locally executed Sentence Transformer model."""

    def __init__(
        self,
        model_identifier: str,
        module_loader: ModuleLoader = import_module,
    ) -> None:
        """Load one model instance for reuse across all encode calls.

        Args:
            model_identifier: Hugging Face or local Sentence Transformer identifier.
            module_loader: Import boundary injectable for deterministic tests.

        Raises:
            SemanticDependencyUnavailableError: If sentence-transformers is unavailable.
            SemanticModelInitializationError: If the model cannot be initialized.
        """
        self.model_identifier = model_identifier
        try:
            module = module_loader("sentence_transformers")
        except ImportError as error:
            raise SemanticDependencyUnavailableError(
                'Semantic support is not installed. Install with ".[semantic]".'
            ) from error

        model_type = cast(type[_SentenceTransformerModel], module.SentenceTransformer)
        try:
            self._model = model_type(model_identifier)
        except (OSError, RuntimeError, ValueError) as error:
            raise SemanticModelInitializationError(
                f"Unable to initialize semantic model {model_identifier!r}: {error}"
            ) from error

    def encode(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        """Batch-encode text and return plain immutable normalized vectors."""
        raw_embeddings = self._model.encode(list(texts), normalize_embeddings=True)
        rows = cast(Iterable[Iterable[float]], raw_embeddings)
        return tuple(tuple(float(value) for value in row) for row in rows)


class SemanticSimilarityBackend:
    """Score text using cached local semantic embeddings."""

    def __init__(self, encoder: SemanticEncoder) -> None:
        """Initialize with one reusable encoder instance."""
        self._encoder = encoder
        self._embedding_cache: dict[str, tuple[float, ...]] = {}

    def score(self, first: str, second: str) -> float:
        """Return affine-normalized cosine similarity in the range 0.0 to 1.0.

        Two empty strings score 1.0. One empty and one non-empty string score 0.0.
        For non-empty strings, cosine similarity in ``[-1, 1]`` is mapped linearly
        to ``[0, 1]``; this preserves ordering without clipping negative values.
        """
        if not first and not second:
            return 1.0
        if not first or not second:
            return 0.0

        first_vector, second_vector = self._embeddings_for((first, second))
        if len(first_vector) != len(second_vector) or not first_vector:
            raise ValueError("Semantic encoder returned incompatible embedding dimensions.")
        cosine = sum(
            first_value * second_value
            for first_value, second_value in zip(first_vector, second_vector, strict=True)
        )
        bounded_cosine = min(1.0, max(-1.0, cosine))
        score = (bounded_cosine + 1.0) / 2.0
        if not math.isfinite(score):
            raise ValueError("Semantic encoder returned a non-finite similarity score.")
        return score

    def _embeddings_for(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        missing = tuple(dict.fromkeys(text for text in texts if text not in self._embedding_cache))
        if missing:
            encoded = self._encoder.encode(missing)
            if len(encoded) != len(missing):
                raise ValueError("Semantic encoder returned an unexpected number of embeddings.")
            self._embedding_cache.update(
                (text, tuple(vector)) for text, vector in zip(missing, encoded, strict=True)
            )
        return tuple(self._embedding_cache[text] for text in texts)
