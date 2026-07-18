# AGENTS.md

These instructions apply to every Codex task in this repository.

---

# Mission

This repository is part of my public engineering portfolio.

Prioritize:

1. Maintainability
2. Readability
3. Testability
4. Simplicity
5. Production-quality engineering

Never optimize for quick hacks over long-term architecture.

---

# Git Workflow (MANDATORY)

Always work on a feature branch.

Before making any code changes:

1. Check the current branch.
2. Check the working tree.
3. Ensure local main is synchronized with origin/main.
4. If currently on main:
   - Pull the latest changes.
   - Create a new feature branch.
   - Switch to that branch.

Suggested branch naming:

- phase-1-modernization
- phase-2-architecture
- phase-3-semantic-alignment
- phase-4-llm-summaries
- feature/<feature-name>
- fix/<bug-name>
- docs/<topic>

Never implement work directly on main.

---

# Git Permissions

Codex MAY:

- create feature branches
- edit files
- run formatting
- run linting
- run typing checks
- run tests
- run coverage
- create local commits
- summarize completed work

Codex MUST NOT:

- commit directly to main
- push directly to main
- merge branches
- merge pull requests
- create pull requests unless explicitly requested
- delete branches
- rewrite history
- force push
- run git reset --hard without explicit permission

Implementation ends after local commits.

I will manually:

- review changes
- push branches
- open pull requests
- merge pull requests
- delete branches

---

# Before Starting

Always report:

- current branch
- git status
- whether working tree is clean
- proposed feature branch

If currently on main:

Create a new feature branch before making any edits.

---

# Architecture

Favor:

- SOLID principles
- composition over inheritance
- dependency injection
- Protocols over abstract base classes when appropriate
- immutable dataclasses where practical
- small focused modules
- explicit interfaces
- clean separation of responsibilities

Avoid:

- giant classes
- giant functions
- duplicated logic
- unnecessary abstractions
- premature optimization

---

# Code Style

Prefer:

- descriptive variable names
- type hints
- Google-style docstrings
- readable code over clever code

Keep functions focused.

If a function is difficult to explain, it is probably doing too much.

---

# Backwards Compatibility

Avoid breaking public APIs unless explicitly instructed.

When refactoring:

- preserve existing interfaces where practical
- create compatibility wrappers if needed
- do not duplicate business logic

---

# Testing

Whenever functionality changes:

- add or update tests
- keep tests deterministic
- prefer dependency injection over mocking when possible

Run:

ruff check .

black --check .

mypy src

pytest

Run coverage if configured.

Fix all failures before finishing.

---

# Documentation

Keep documentation synchronized with implementation.

Update README when appropriate.

Update architecture documentation whenever architecture changes.

---

# Before Finishing

Report:

- branch name
- commits created
- files changed
- tests run
- lint results
- typing results
- coverage results
- remaining technical debt
- recommended next phase

Then provide the exact git commands I should run next.

Do not merge anything.

Stop after local commits are complete.

---

# Decision Making

If a major architectural decision is required:

STOP.

Explain:

- the options
- tradeoffs
- recommendation

Wait for approval before implementing significant architectural changes.

---

# Repository Goal

This repository should be representative of production-quality engineering.

Every change should improve:

- maintainability
- clarity
- extensibility
- correctness
- testability

When in doubt, optimize for the engineer who will read this code two years from now.


# Collaboration Workflow

ChatGPT is responsible for:

- architecture
- software design
- roadmap planning
- code review
- documentation strategy
- engineering decisions

Codex is responsible for:

- implementing approved designs
- refactoring
- writing tests
- running tooling
- fixing lint/type/test failures
- creating local commits

If implementation reveals an architectural issue, stop and explain it instead of making assumptions.