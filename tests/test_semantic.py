"""Tests for the optional local semantic similarity backend."""

from collections.abc import Sequence
from types import ModuleType

import pytest

from src.semantic import (
    SemanticDependencyUnavailableError,
    SemanticSimilarityBackend,
    SentenceTransformerEncoder,
)
from src.similarity import SimilarityBackend


class MappingEncoder:
    """Return controlled unit vectors without loading an external model."""

    def __init__(self, embeddings: dict[str, tuple[float, ...]]) -> None:
        self.embeddings = embeddings
        self.calls: list[tuple[str, ...]] = []

    def encode(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        self.calls.append(tuple(texts))
        return tuple(self.embeddings[text] for text in texts)


def test_semantic_backend_satisfies_similarity_protocol_and_score_range() -> None:
    encoder = MappingEncoder(
        {
            "first": (1.0, 0.0),
            "same": (1.0, 0.0),
            "orthogonal": (0.0, 1.0),
            "opposite": (-1.0, 0.0),
        }
    )
    backend: SimilarityBackend = SemanticSimilarityBackend(encoder)

    assert backend.score("first", "same") == 1.0
    assert backend.score("first", "orthogonal") == 0.5
    assert backend.score("first", "opposite") == 0.0


def test_semantic_backend_handles_empty_strings_without_encoding() -> None:
    encoder = MappingEncoder({})
    backend = SemanticSimilarityBackend(encoder)

    assert backend.score("", "") == 1.0
    assert backend.score("text", "") == 0.0
    assert backend.score("", "text") == 0.0
    assert encoder.calls == []


def test_semantic_backend_batches_and_caches_embeddings() -> None:
    encoder = MappingEncoder({"first": (1.0, 0.0), "second": (0.0, 1.0)})
    backend = SemanticSimilarityBackend(encoder)

    backend.score("first", "second")
    backend.score("first", "second")

    assert encoder.calls == [("first", "second")]


def test_sentence_transformer_model_initializes_once_per_encoder() -> None:
    class FakeModel:
        initialization_count = 0

        def __init__(self, model_identifier: str) -> None:
            self.model_identifier = model_identifier
            FakeModel.initialization_count += 1

        def encode(self, sentences: list[str], *, normalize_embeddings: bool) -> list[list[float]]:
            assert normalize_embeddings is True
            return [[1.0, 0.0] for _ in sentences]

    module = ModuleType("sentence_transformers")
    module.__dict__["SentenceTransformer"] = FakeModel
    encoder = SentenceTransformerEncoder("test-model", module_loader=lambda _: module)
    backend = SemanticSimilarityBackend(encoder)

    backend.score("one", "two")
    backend.score("three", "four")

    assert FakeModel.initialization_count == 1


def test_sentence_transformer_dependency_absence_has_useful_error() -> None:
    def missing_module(_: str) -> ModuleType:
        raise ModuleNotFoundError("sentence_transformers")

    with pytest.raises(SemanticDependencyUnavailableError, match="semantic"):
        SentenceTransformerEncoder("test-model", module_loader=missing_module)


def test_semantic_backend_rejects_invalid_encoder_output() -> None:
    encoder = MappingEncoder({"first": (1.0,), "second": (1.0, 0.0)})

    with pytest.raises(ValueError, match="dimensions"):
        SemanticSimilarityBackend(encoder).score("first", "second")
