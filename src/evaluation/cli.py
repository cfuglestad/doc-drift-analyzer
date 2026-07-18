"""Command-line accuracy evaluation for configured similarity backends."""

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from src.config import (
    DEFAULT_SEMANTIC_MODEL,
    AlignmentConfig,
    SimilarityBackendType,
    build_backend,
)
from src.evaluation.dataset import load_evaluation_dataset
from src.evaluation.metrics import evaluate_backend
from src.evaluation.models import BackendEvaluationResult

DEFAULT_DATASET_PATH = Path("evaluation/data/alignment_cases.json")


def main(arguments: Sequence[str] | None = None) -> int:
    """Run deterministic accuracy evaluation and optionally write JSON results."""
    parser = _build_parser()
    options = parser.parse_args(arguments)
    backend_type = SimilarityBackendType(options.backend)
    thresholds = (
        _parse_thresholds(options.thresholds)
        if options.thresholds is not None
        else _default_thresholds(backend_type)
    )
    dataset = load_evaluation_dataset(options.dataset)
    model_identifier = options.model_identifier or DEFAULT_SEMANTIC_MODEL
    selection = build_backend(
        AlignmentConfig(
            backend=backend_type,
            fallback_to_lexical=False,
            model_identifier=model_identifier,
        )
    )
    results = tuple(
        evaluate_backend(
            dataset=dataset,
            backend=selection.backend,
            backend_name=backend_type.value,
            threshold=threshold,
        )
        for threshold in thresholds
    )
    best_result = select_recommended_result(results)
    payload = {
        "dataset": dataset.name,
        "backend": backend_type.value,
        "model_identifier": (
            model_identifier if backend_type is not SimilarityBackendType.LEXICAL else None
        ),
        "results": [asdict(result) for result in results],
        "recommended": asdict(best_result),
    }
    rendered = json.dumps(payload, indent=2)
    if options.output is not None:
        options.output.parent.mkdir(parents=True, exist_ok=True)
        options.output.write_text(f"{rendered}\n", encoding="utf-8")
    print(rendered)
    return 0


def select_recommended_result(
    results: Sequence[BackendEvaluationResult],
) -> BackendEvaluationResult:
    """Select a threshold deterministically from generated evaluation metrics."""
    if not results:
        raise ValueError("At least one evaluation result is required.")
    return max(
        results,
        key=lambda result: (
            result.metrics.match_f1,
            result.metrics.exact_match_accuracy,
            result.metrics.added_section_accuracy,
            result.metrics.removed_section_accuracy,
            -result.metrics.false_matches,
            -result.metrics.missed_matches,
            -result.metrics.unsupported_predictions,
            -result.threshold,
        ),
    )


def _parse_thresholds(value: str) -> tuple[float, ...]:
    thresholds = tuple(float(item.strip()) for item in value.split(",") if item.strip())
    if not thresholds or any(not 0.0 <= threshold <= 1.0 for threshold in thresholds):
        raise argparse.ArgumentTypeError("Thresholds must be comma-separated values from 0 to 1.")
    return thresholds


def _default_thresholds(backend: SimilarityBackendType) -> tuple[float, ...]:
    return {
        SimilarityBackendType.LEXICAL: (0.25, 0.35, 0.40, 0.45, 0.55, 0.65, 0.75),
        SimilarityBackendType.SEMANTIC: (0.55, 0.60, 0.65, 0.70, 0.76, 0.80, 0.85),
        SimilarityBackendType.HYBRID: (0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70),
    }[backend]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backend",
        choices=[backend.value for backend in SimilarityBackendType],
        required=True,
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument(
        "--thresholds",
        default=None,
        help="Comma-separated thresholds; defaults to a backend-specific sweep.",
    )
    parser.add_argument("--model-identifier", default=None)
    parser.add_argument("--output", type=Path)
    return parser
