"""Tests for rule-based section extraction."""

from src.models import Section
from src.sectioning import extract_sections


def test_extract_sections_recognizes_all_caps_and_numbered_headings() -> None:
    text = "Preface text\n\nPOLICY\nPolicy body\n1.2 Scope\nScope body"

    assert extract_sections(text) == [
        Section(title="Introduction", content="Preface text"),
        Section(title="POLICY", content="Policy body"),
        Section(title="1.2 Scope", content="Scope body"),
    ]


def test_extract_sections_uses_introduction_when_no_heading_exists() -> None:
    assert extract_sections("First paragraph\nSecond line") == [
        Section(title="Introduction", content="First paragraph\nSecond line")
    ]


def test_extract_sections_ignores_headings_without_content() -> None:
    assert extract_sections("FIRST HEADING\nSECOND HEADING\nBody") == [
        Section(title="SECOND HEADING", content="Body")
    ]


def test_extract_sections_discards_empty_input() -> None:
    assert extract_sections("\n\n") == []
