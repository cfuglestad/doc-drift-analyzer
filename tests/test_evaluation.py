"""Tests for labeled dataset loading and deterministic accuracy metrics."""

from pathlib import Path

from src.evaluation.dataset import load_evaluation_dataset
from src.evaluation.metrics import evaluate_backend
from src.evaluation.models import (
    AlignmentLabel,
    EvaluationDataset,
    EvaluationDocumentPair,
    EvaluationExample,
    EvaluationSection,
)

DATASET_PATH = Path("evaluation/data/alignment_cases.json")


class PairScoreBackend:
    """Return controlled scores for exact text pairs."""

    def __init__(self, matching_pairs: set[tuple[str, str]]) -> None:
        self.matching_pairs = matching_pairs

    def score(self, first: str, second: str) -> float:
        return 1.0 if (first, second) in self.matching_pairs else 0.0


def test_versioned_dataset_covers_supported_and_analysis_labels() -> None:
    dataset = load_evaluation_dataset(DATASET_PATH)
    labels = {example.relationship for pair in dataset.document_pairs for example in pair.examples}

    assert dataset.name == "synthetic-alignment-cases-v1"
    assert len(dataset.document_pairs) == 5
    assert labels == set(AlignmentLabel)


def test_metrics_report_perfect_supported_alignment() -> None:
    dataset = _supported_dataset()
    backend = PairScoreBackend(
        {
            ("Match old", "Match new"),
            ("Same concept", "Equivalent concept"),
        }
    )

    metrics = evaluate_backend(dataset, backend, "controlled", threshold=0.5).metrics

    assert metrics.match_precision == 1.0
    assert metrics.match_recall == 1.0
    assert metrics.match_f1 == 1.0
    assert metrics.exact_match_accuracy == 1.0
    assert metrics.added_section_accuracy == 1.0
    assert metrics.removed_section_accuracy == 1.0
    assert metrics.false_matches == 0
    assert metrics.missed_matches == 0


def test_metrics_count_false_and_missed_matches() -> None:
    dataset = _supported_dataset()
    backend = PairScoreBackend(
        {
            ("Match old", "Added new"),
            ("Same concept", "Added content"),
            ("Removed old", "Match new"),
            ("Removed content", "Equivalent concept"),
        }
    )

    metrics = evaluate_backend(dataset, backend, "wrong", threshold=0.5).metrics

    assert metrics.match_precision == 0.0
    assert metrics.match_recall == 0.0
    assert metrics.false_matches == 2
    assert metrics.missed_matches == 1
    assert metrics.added_section_accuracy == 0.0
    assert metrics.removed_section_accuracy == 0.0


def test_unsupported_relationships_are_reported_separately() -> None:
    dataset = EvaluationDataset(
        name="unsupported",
        document_pairs=(
            EvaluationDocumentPair(
                identifier="ambiguous",
                old_sections=(EvaluationSection("old", "Old", "Old"),),
                new_sections=(
                    EvaluationSection("new-a", "A", "A"),
                    EvaluationSection("new-b", "B", "B"),
                ),
                examples=(
                    EvaluationExample(
                        document_pair_id="ambiguous",
                        old_section_ids=("old",),
                        new_section_ids=("new-a", "new-b"),
                        relationship=AlignmentLabel.AMBIGUOUS,
                    ),
                ),
            ),
        ),
    )

    metrics = evaluate_backend(
        dataset, PairScoreBackend(set()), "controlled", threshold=0.5
    ).metrics

    assert metrics.ambiguous_examples == 1
    assert metrics.false_matches == 0
    assert metrics.missed_matches == 0
    assert metrics.unsupported_predictions == 3


def _supported_dataset() -> EvaluationDataset:
    return EvaluationDataset(
        name="supported",
        document_pairs=(
            EvaluationDocumentPair(
                identifier="pair",
                old_sections=(
                    EvaluationSection("match-old", "Match old", "Same concept"),
                    EvaluationSection("removed-old", "Removed old", "Removed content"),
                ),
                new_sections=(
                    EvaluationSection("match-new", "Match new", "Equivalent concept"),
                    EvaluationSection("added-new", "Added new", "Added content"),
                ),
                examples=(
                    EvaluationExample(
                        "pair",
                        ("match-old",),
                        ("match-new",),
                        AlignmentLabel.MATCHED,
                    ),
                    EvaluationExample("pair", ("removed-old",), (), AlignmentLabel.REMOVED),
                    EvaluationExample("pair", (), ("added-new",), AlignmentLabel.ADDED),
                ),
            ),
        ),
    )
