# Alignment evaluation and benchmark

## Scope

Results were generated from `evaluation/data/alignment_cases.json`, a synthetic,
redistributable dataset with five document pairs. It covers unchanged and lightly edited
sections, semantic rewrites, renamed and reordered headings, additions, removals, unrelated
content, boilerplate, ambiguous matches, splits, and merges.

The aligner remains one-to-one. One ambiguous, one split, and one merged example are counted
and reported separately; they are excluded from ordinary match, added, and removed errors.

## Metric definitions

- **Match precision:** correct predicted one-to-one pairs divided by predicted pairs. It is
  `0` when expected matches exist but the backend predicts none.
- **Match recall:** correct predicted pairs divided by expected supported pairs.
- **Match F1:** harmonic mean of match precision and recall.
- **Exact match accuracy:** proportion of document pairs whose supported matched, added,
  and removed sets are all exactly correct.
- **Added/removed accuracy:** correctly identified expected additions or removals divided by
  the respective expected count.
- **False matches:** predicted supported pairs absent from the labels.
- **Missed matches:** expected supported pairs absent from predictions.
- **Unsupported predictions:** alignment decisions touching ambiguous, split, or merged IDs.

## Accuracy results

| Backend | Threshold | Precision | Recall | F1 | Exact | Added | Removed | False | Missed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Lexical | 0.40 | 1.000 | 0.571 | 0.727 | 0.600 | 1.000 | 1.000 | 0 | 3 |
| Semantic | 0.65 | 0.875 | 1.000 | 0.933 | 0.800 | 0.667 | 0.500 | 1 | 0 |
| Hybrid 50/50 | 0.50 | 0.875 | 1.000 | 0.933 | 0.800 | 0.667 | 0.500 | 1 | 0 |

The lexical application default remains `0.35` for compatibility; at that value it scored
precision `0.714`, recall `0.714`, F1 `0.714`, exact accuracy `0.400`, added accuracy
`0.667`, and removed accuracy `0.000`.

Semantic `0.65` is recommended when recall of heavily rewritten equivalent sections is the
priority. Semantic `0.76` is a higher-precision alternative: precision `1.000`, recall
`0.857`, F1 `0.923`, and perfect added/removed accuracy. The hybrid did not outperform
semantic, so semantic is the simpler optional recommendation. Lexical remains the default
for compatibility, predictable resource use, and offline use without a model.

## Performance observations

Environment:

- Windows 10 build 26100
- Python 3.12.10
- Intel Core i5-8250U, 4 cores / 8 logical processors
- approximately 8 GB system memory
- CPU-only execution
- sentence-transformers 5.6.0, transformers 5.14.1, torch 2.13.0

| Backend | Init | Cold align | Warm align | Avg score | Avg document pair | Approx. peak memory |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Lexical | 0.00005 s | 0.0302 s | 0.0211 s | 0.00049 s | 0.0155 s | 12 KiB |
| Semantic | 88.946 s | 0.7109 s | 0.0090 s | 0.01418 s | 0.0809 s | 237.6 MiB |
| Hybrid | 105.586 s | 1.0261 s | 0.0467 s | 0.01213 s | 0.1010 s | 237.6 MiB |

Semantic and hybrid used five timed rounds; lexical used ten. Initialization included model
construction from a populated local cache and Hugging Face availability checks. Timings
were collected with `tracemalloc`, which adds overhead; memory excludes some native tensor
allocations. Results are machine-sensitive observations and do not gate CI.

## Reproduction

```bash
python -m pip install -e ".[dev,semantic]"
python -m src.evaluation --backend lexical --output evaluation/results/lexical.json
python -m src.evaluation --backend semantic --output evaluation/results/semantic.json
python -m src.evaluation --backend hybrid --output evaluation/results/hybrid.json
python -m src.benchmark --backend lexical --threshold 0.35 --rounds 10
python -m src.benchmark --backend semantic --threshold 0.65 --rounds 5
python -m src.benchmark --backend hybrid --threshold 0.50 --rounds 5
```

Raw generated JSON is versioned under `evaluation/results/`.
