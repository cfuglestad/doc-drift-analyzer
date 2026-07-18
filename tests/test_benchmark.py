"""Tests for the reproducible benchmark command."""

import json
from pathlib import Path

from src.benchmark import main


def test_benchmark_command_executes_on_tiny_lexical_fixture(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "benchmark.json"

    exit_code = main(
        [
            "--backend",
            "lexical",
            "--rounds",
            "1",
            "--output",
            str(output_path),
        ]
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["backend"] == "lexical"
    assert payload["rounds"] == 1
    assert payload["initialization_seconds"] >= 0.0
    assert payload["approximate_peak_memory_bytes"] > 0
