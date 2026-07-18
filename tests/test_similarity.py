"""Tests for similarity interfaces and implementations."""

import difflib

from src.similarity import LexicalSimilarityBackend, SimilarityBackend


def test_lexical_backend_preserves_sequence_matcher_behavior() -> None:
    backend = LexicalSimilarityBackend()

    assert backend.score("same", "same") == 1.0
    assert backend.score("abc", "xyz") == 0.0
    assert (
        backend.score("policy", "policies")
        == difflib.SequenceMatcher(None, "policy", "policies").ratio()
    )


def test_lexical_backend_structurally_satisfies_protocol() -> None:
    backend: SimilarityBackend = LexicalSimilarityBackend()

    assert backend.score("text", "text") == 1.0
