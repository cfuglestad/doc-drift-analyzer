# Phase 2: Alignment and summarization interfaces

## Decision

Doc Drift Analyzer uses structural protocols and constructor injection for similarity and
summarization behavior. The default implementations preserve the original lexical matching
algorithm and deterministic summary wording.

## Why protocols

`SimilarityBackend` and `ChangeSummarizer` describe the behavior their consumers require
without forcing implementations into an inheritance hierarchy. This keeps adapters small,
supports simple test fakes, and avoids coupling future semantic implementations to base
class construction or shared state. Abstract base classes can be introduced later only if
runtime enforcement or shared implementation becomes necessary.

## Why constructor injection

`SectionAligner` receives its similarity backend explicitly. Dependencies are therefore
visible at the composition point, deterministic in tests, and independent of global
configuration, registries, service locators, or framework lifecycle behavior.

## Responsibility boundaries

- `SimilarityBackend` scores two strings and knows nothing about thresholds or sections.
- `LexicalSimilarityBackend` encapsulates the existing `difflib.SequenceMatcher` behavior.
- `SectionAligner` owns greedy pairing, the title/body weighting, thresholds, and unmatched
  section handling.
- `diffing` owns change labels and word-level presentation diffs.
- `ChangeSummarizer` defines conversion from alignments to a typed summary.
- `RuleBasedChangeSummarizer` owns established counts and bullet wording.
- Frozen domain models carry sections, alignments, and summaries through the core path.
- Compatibility functions adapt legacy dictionaries without duplicating business logic.

## Deferred work

This phase intentionally excludes embeddings, model providers, vector stores, backend
registries, new matching algorithms, UI features, and changes to visible labels or summary
wording. It also does not select a semantic model or define model lifecycle management.

## Future semantic similarity

A semantic backend will implement `SimilarityBackend.score` and can be passed directly to
`SectionAligner`. Before adding one, the project should establish a labeled alignment
evaluation set, quality metrics, performance limits, and configuration for choosing a
backend. Alignment policy and summarization should not need to change.
