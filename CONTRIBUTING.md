# Contributing to Doc Drift Analyzer

Thank you for helping improve Doc Drift Analyzer. Contributions should be focused,
well-tested, and compatible with the project's existing behavior and architecture.

## Development workflow

1. Fork the repository and create a focused branch from `main`.
2. Create and activate a Python 3.12 virtual environment.
3. Install the project with `python -m pip install -e ".[dev]"`.
4. Install local hooks with `pre-commit install`.
5. Add or update tests for every behavioral change.
6. Run the complete quality suite before opening a pull request.

```bash
ruff check .
black --check .
mypy src
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

## Engineering expectations

- Preserve existing user-visible behavior unless the change explicitly proposes otherwise.
- Keep functions focused, typed, and documented with Google-style docstrings where useful.
- Prefer incremental improvements over broad rewrites or premature abstractions.
- Keep NLP backends modular so future semantic approaches can coexist with lexical methods.
- Include clear tests for edge cases and failure modes.

## Pull requests

Use a descriptive title and explain:

- what changed and why;
- how the change was validated;
- any compatibility considerations or limitations;
- related issues, if applicable.

Keep commits small and logically scoped. Do not commit credentials, private documents,
proprietary datasets, generated coverage output, or local environment files.

