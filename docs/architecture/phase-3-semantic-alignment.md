# Phase 3: Evidence-based semantic alignment

## Decision

Doc Drift Analyzer adds `sentence-transformers/all-MiniLM-L6-v2` as an optional local
semantic backend. Lexical similarity remains the application default. A transparent 50/50
hybrid is available for comparison but is not preferred because it did not improve the
initial evaluation.

## Why evaluation came first

Semantic similarity changes score distributions and deployment cost. The project therefore
introduced labeled, redistributable document pairs and deterministic metrics before model
integration. Backend thresholds and recommendations come from generated results in
`evaluation/results/`, not intuition alone. The dataset is intentionally small, so results
guide Phase 3 defaults rather than establish broad production validity.

## Model selection and scores

`all-MiniLM-L6-v2` was selected because it is a widely supported Sentence Transformers
model intended for sentence and paragraph embeddings, produces compact 384-dimensional
vectors, and is practical for CPU-only local inference. Its model card states that inputs
beyond 256 word pieces are truncated.

The encoder returns unit-normalized vectors. Cosine similarity in `[-1, 1]` is mapped with
`(cosine + 1) / 2` to `[0, 1]`. This affine mapping preserves ordering and negative-score
information. Two empty strings score `1.0`; one empty string scores `0.0`. Semantic and
lexical thresholds remain separate because their score meanings differ.

## Backend selection and hybrid design

`AlignmentConfig` explicitly selects `lexical`, `semantic`, or `hybrid`. Construction uses
one readable factory rather than registries, dynamic imports, or a dependency-injection
framework. Thresholds stay outside similarity implementations.

The hybrid score is:

```text
0.5 * lexical_score + 0.5 * semantic_score
```

Weights must be finite, non-negative, and sum to one. No learned ranker is introduced.
Equal weighting is an evaluation baseline, not a claim that hybrid scoring is superior.

## Model lifecycle and caching

`SentenceTransformerEncoder` loads one model in its constructor. A
`SemanticSimilarityBackend` reuses that encoder, batches the two missing texts in each score
operation, and caches embeddings by exact text for the backend lifetime. It makes no network
call during scoring after initialization.

The core backend has no Streamlit dependency. Streamlit applies `st.cache_resource` at the
composition layer so threshold changes do not reload the model. Model files normally use
the Hugging Face cache; offline deployments must pre-populate that cache or configure a
local model path. Cache invalidation follows the configured model identifier and upstream
cache revision behavior.

## Fallback policy

Semantic dependencies and model initialization can fail because a package, model, cache,
network resource, or local resource is unavailable. `build_backend` catches typed semantic
initialization failures only. With fallback enabled, it returns lexical similarity plus
`FallbackMetadata` containing the requested backend, active backend, reason, and diagnostic
message. Streamlit displays that state without logging document text.

Evaluation and benchmark commands disable fallback, ensuring model failures remain visible.

## Privacy

- Embedding inference occurs locally; document contents are not sent to an external API.
- Initial model download may contact Hugging Face.
- Cached model files contain model assets, not uploaded documents.
- Backends do not log document text or full section content.
- A future hosted provider would require a separate privacy and threat review.

## Deployment constraints

- The evaluated model cache occupied approximately 87 MiB on Windows; the PyTorch runtime
  makes environments and container images substantially larger.
- CPU inference is supported but adds cold-start and per-document latency.
- The local benchmark observed roughly 238 MiB of Python-traced peak memory, which excludes
  some native tensor allocations and is therefore only an approximation.
- Each worker process can hold its own model copy, affecting concurrent deployments.
- Streamlit Community Cloud or similarly constrained hosts may have slow starts or limited
  memory and ephemeral caches.
- Offline images should include the model cache and semantic dependencies at build time.
- GPU execution may be selected by the underlying model runtime, but this phase adds no
  GPU-specific configuration.

## Intentionally deferred

This phase does not add hosted providers, fine-tuning, learned ranking, arbitrary plugin
discovery, many-to-many alignment, confidence calibration, corpus-scale embedding batches,
or production timing gates. Split and merged labels remain analysis-only because the
production aligner remains deterministic and one-to-one.
