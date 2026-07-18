"""Reproducible, non-blocking performance observations for alignment backends."""

import argparse
import json
import time
import tracemalloc
from collections.abc import Callable, Sequence
from dataclasses import asdict
from pathlib import Path

from src.alignment import SectionAligner
from src.config import (
    DEFAULT_SEMANTIC_MODEL,
    AlignmentConfig,
    BackendSelection,
    SimilarityBackendType,
    build_backend,
)
from src.evaluation.dataset import load_evaluation_dataset
from src.evaluation.models import BenchmarkResult, EvaluationDataset

DEFAULT_DATASET_PATH = Path("evaluation/data/alignment_cases.json")


def benchmark_backend(
    dataset: EvaluationDataset,
    backend_factory: Callable[[], BackendSelection],
    rounds: int,
) -> BenchmarkResult:
    """Measure initialization, cold/warm alignment, scoring, and Python memory.

    Timings are observations rather than pass/fail thresholds. Approximate peak memory is
    measured by ``tracemalloc`` and may exclude native tensor allocations.
    """
    if rounds < 1:
        raise ValueError("Benchmark rounds must be at least one.")

    tracemalloc.start()
    initialization_start = time.perf_counter()
    selection = backend_factory()
    initialization_seconds = time.perf_counter() - initialization_start
    aligner = SectionAligner(similarity_backend=selection.backend)
    first_pair = dataset.document_pairs[0]
    old_sections = [section.as_section() for section in first_pair.old_sections]
    new_sections = [section.as_section() for section in first_pair.new_sections]

    cold_start = time.perf_counter()
    aligner.align(old_sections, new_sections, selection.threshold)
    cold_alignment_seconds = time.perf_counter() - cold_start

    warm_start = time.perf_counter()
    for _ in range(rounds):
        aligner.align(old_sections, new_sections, selection.threshold)
    warm_alignment_seconds = (time.perf_counter() - warm_start) / rounds

    scoring_start = time.perf_counter()
    for _ in range(rounds):
        selection.backend.score("policy records", "document retention")
    average_scoring_seconds = (time.perf_counter() - scoring_start) / rounds

    document_start = time.perf_counter()
    for _ in range(rounds):
        for document_pair in dataset.document_pairs:
            aligner.align(
                [section.as_section() for section in document_pair.old_sections],
                [section.as_section() for section in document_pair.new_sections],
                selection.threshold,
            )
    document_pair_alignment_seconds = (
        (time.perf_counter() - document_start) / rounds / len(dataset.document_pairs)
    )
    _, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return BenchmarkResult(
        backend=selection.active_backend.value,
        threshold=selection.threshold,
        initialization_seconds=initialization_seconds,
        cold_alignment_seconds=cold_alignment_seconds,
        warm_alignment_seconds=warm_alignment_seconds,
        average_scoring_seconds=average_scoring_seconds,
        document_pair_alignment_seconds=document_pair_alignment_seconds,
        approximate_peak_memory_bytes=peak_memory,
        rounds=rounds,
    )


def main(arguments: Sequence[str] | None = None) -> int:
    """Run a backend benchmark and optionally write its JSON result."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backend",
        choices=[backend.value for backend in SimilarityBackendType],
        required=True,
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--threshold", type=float)
    parser.add_argument("--model-identifier", default=DEFAULT_SEMANTIC_MODEL)
    parser.add_argument("--output", type=Path)
    options = parser.parse_args(arguments)
    backend_type = SimilarityBackendType(options.backend)
    dataset = load_evaluation_dataset(options.dataset)
    config = AlignmentConfig(
        backend=backend_type,
        threshold=options.threshold,
        fallback_to_lexical=False,
        model_identifier=options.model_identifier,
    )
    result = benchmark_backend(dataset, lambda: build_backend(config), options.rounds)
    rendered = json.dumps(asdict(result), indent=2)
    if options.output is not None:
        options.output.parent.mkdir(parents=True, exist_ok=True)
        options.output.write_text(f"{rendered}\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
