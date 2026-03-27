# doc-drift-analyzer

A lightweight NLP app for comparing two versions of a document and surfacing meaningful changes.

## Features

- Upload TXT, PDF, or DOCX files
- Extract and normalize text
- Split documents into sections and paragraphs
- Align similar content across versions
- Detect added, removed, minor, and major changes
- View inline word-level differences
- Generate a concise summary of major edits

## Use cases

- Policy updates
- SOP revisions
- Contract drafts
- Internal documentation changes
- General version comparison

## Project structure

- `app/streamlit_app.py` — Streamlit front end
- `src/` — reusable comparison logic
- `tests/` — lightweight tests
- `sample_data/` — example inputs

## Installation

```bash
pip install -r requirements.txt
