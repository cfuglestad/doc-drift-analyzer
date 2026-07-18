"""Deterministic alignment accuracy metrics."""

from collections.abc import Sequence

from src.alignment import SectionAligner
from src.evaluation.models import (
    AlignmentLabel,
    AlignmentMetrics,
    BackendEvaluationResult,
    EvaluationDataset,
    EvaluationDocumentPair,
)
from src.models import AlignmentResult
from src.similarity import SimilarityBackend


def evaluate_backend(
    dataset: EvaluationDataset,
    backend: SimilarityBackend,
    backend_name: str,
    threshold: float,
) -> BackendEvaluationResult:
    """Evaluate one backend and threshold against supported one-to-one labels."""
    expected_matches: set[tuple[str, str, str]] = set()
    predicted_matches: set[tuple[str, str, str]] = set()
    expected_added: set[tuple[str, str]] = set()
    predicted_added: set[tuple[str, str]] = set()
    expected_removed: set[tuple[str, str]] = set()
    predicted_removed: set[tuple[str, str]] = set()
    exact_documents = 0
    ambiguous_examples = 0
    split_examples = 0
    merged_examples = 0
    unsupported_predictions = 0

    aligner = SectionAligner(similarity_backend=backend)
    for document_pair in dataset.document_pairs:
        expected = _expected_relationships(document_pair)
        expected_matches.update(
            (document_pair.identifier, old_id, new_id) for old_id, new_id in expected.matches
        )
        expected_added.update((document_pair.identifier, new_id) for new_id in expected.added)
        expected_removed.update((document_pair.identifier, old_id) for old_id in expected.removed)
        ambiguous_examples += expected.ambiguous_examples
        split_examples += expected.split_examples
        merged_examples += expected.merged_examples

        results = aligner.align(
            [section.as_section() for section in document_pair.old_sections],
            [section.as_section() for section in document_pair.new_sections],
            threshold=threshold,
        )
        predicted = _predicted_relationships(document_pair, results, expected.unsupported_ids)
        predicted_matches.update(
            (document_pair.identifier, old_id, new_id) for old_id, new_id in predicted.matches
        )
        predicted_added.update((document_pair.identifier, new_id) for new_id in predicted.added)
        predicted_removed.update((document_pair.identifier, old_id) for old_id in predicted.removed)
        unsupported_predictions += predicted.unsupported_predictions
        if (
            predicted.matches == expected.matches
            and predicted.added == expected.added
            and predicted.removed == expected.removed
        ):
            exact_documents += 1

    true_matches = expected_matches & predicted_matches
    false_matches = predicted_matches - expected_matches
    missed_matches = expected_matches - predicted_matches
    precision = (
        _safe_ratio(len(true_matches), len(predicted_matches))
        if predicted_matches
        else float(not expected_matches)
    )
    recall = _safe_ratio(len(true_matches), len(expected_matches))
    f1 = _safe_ratio(2 * precision * recall, precision + recall)

    return BackendEvaluationResult(
        backend=backend_name,
        threshold=threshold,
        metrics=AlignmentMetrics(
            match_precision=precision,
            match_recall=recall,
            match_f1=f1,
            exact_match_accuracy=_safe_ratio(exact_documents, len(dataset.document_pairs)),
            added_section_accuracy=_safe_ratio(
                len(expected_added & predicted_added), len(expected_added)
            ),
            removed_section_accuracy=_safe_ratio(
                len(expected_removed & predicted_removed), len(expected_removed)
            ),
            false_matches=len(false_matches),
            missed_matches=len(missed_matches),
            ambiguous_examples=ambiguous_examples,
            split_examples=split_examples,
            merged_examples=merged_examples,
            unsupported_predictions=unsupported_predictions,
        ),
    )


class _Relationships:
    """Mutable accumulator scoped to one document pair."""

    def __init__(self) -> None:
        self.matches: set[tuple[str, str]] = set()
        self.added: set[str] = set()
        self.removed: set[str] = set()
        self.unsupported_ids: set[str] = set()
        self.ambiguous_examples = 0
        self.split_examples = 0
        self.merged_examples = 0
        self.unsupported_predictions = 0


def _expected_relationships(document_pair: EvaluationDocumentPair) -> _Relationships:
    relationships = _Relationships()
    for example in document_pair.examples:
        if example.relationship is AlignmentLabel.MATCHED:
            relationships.matches.add((example.old_section_ids[0], example.new_section_ids[0]))
        elif example.relationship is AlignmentLabel.ADDED:
            relationships.added.add(example.new_section_ids[0])
        elif example.relationship is AlignmentLabel.REMOVED:
            relationships.removed.add(example.old_section_ids[0])
        else:
            relationships.unsupported_ids.update(example.old_section_ids)
            relationships.unsupported_ids.update(example.new_section_ids)
            if example.relationship is AlignmentLabel.AMBIGUOUS:
                relationships.ambiguous_examples += 1
            elif example.relationship is AlignmentLabel.SPLIT:
                relationships.split_examples += 1
            elif example.relationship is AlignmentLabel.MERGED:
                relationships.merged_examples += 1
    return relationships


def _predicted_relationships(
    document_pair: EvaluationDocumentPair,
    results: Sequence[AlignmentResult],
    unsupported_ids: set[str],
) -> _Relationships:
    relationships = _Relationships()
    old_ids = [section.identifier for section in document_pair.old_sections]
    new_ids = [section.identifier for section in document_pair.new_sections]
    for result in results:
        old_id = old_ids[result.old_index] if result.old_index is not None else None
        new_id = new_ids[result.new_index] if result.new_index is not None else None
        involved_ids = {identifier for identifier in (old_id, new_id) if identifier is not None}
        if involved_ids & unsupported_ids:
            relationships.unsupported_predictions += 1
            continue
        if old_id is not None and new_id is not None:
            relationships.matches.add((old_id, new_id))
        elif old_id is not None:
            relationships.removed.add(old_id)
        elif new_id is not None:
            relationships.added.add(new_id)
    return relationships


def _safe_ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 1.0
