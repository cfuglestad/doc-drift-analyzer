"""Typed models used only by alignment evaluation and benchmarking."""

from dataclasses import dataclass
from enum import StrEnum

from src.models import Section


class AlignmentLabel(StrEnum):
    """Expected relationship between labeled old and new sections."""

    MATCHED = "matched"
    ADDED = "added"
    REMOVED = "removed"
    AMBIGUOUS = "ambiguous"
    SPLIT = "split"
    MERGED = "merged"


@dataclass(frozen=True, slots=True)
class EvaluationSection:
    """A section with a stable identifier for evaluation."""

    identifier: str
    title: str
    content: str

    def as_section(self) -> Section:
        """Return the production section representation."""
        return Section(title=self.title, content=self.content)


@dataclass(frozen=True, slots=True)
class EvaluationExample:
    """One labeled relationship within a document pair."""

    document_pair_id: str
    old_section_ids: tuple[str, ...]
    new_section_ids: tuple[str, ...]
    relationship: AlignmentLabel
    difficulty: str | None = None
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class EvaluationDocumentPair:
    """Two ordered section collections and their expected relationships."""

    identifier: str
    old_sections: tuple[EvaluationSection, ...]
    new_sections: tuple[EvaluationSection, ...]
    examples: tuple[EvaluationExample, ...]


@dataclass(frozen=True, slots=True)
class EvaluationDataset:
    """A named, version-controlled collection of labeled document pairs."""

    name: str
    document_pairs: tuple[EvaluationDocumentPair, ...]


@dataclass(frozen=True, slots=True)
class AlignmentMetrics:
    """Deterministic aggregate metrics for one backend and threshold."""

    match_precision: float
    match_recall: float
    match_f1: float
    exact_match_accuracy: float
    added_section_accuracy: float
    removed_section_accuracy: float
    false_matches: int
    missed_matches: int
    ambiguous_examples: int
    split_examples: int
    merged_examples: int
    unsupported_predictions: int


@dataclass(frozen=True, slots=True)
class BackendEvaluationResult:
    """Accuracy results for a configured backend at one threshold."""

    backend: str
    threshold: float
    metrics: AlignmentMetrics


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Machine-sensitive performance observations for one backend."""

    backend: str
    threshold: float
    initialization_seconds: float
    cold_alignment_seconds: float
    warm_alignment_seconds: float
    average_scoring_seconds: float
    document_pair_alignment_seconds: float
    approximate_peak_memory_bytes: int
    rounds: int


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    """Accuracy and performance results generated from one dataset."""

    dataset_name: str
    accuracy_results: tuple[BackendEvaluationResult, ...]
    benchmarks: tuple[BenchmarkResult, ...] = ()
