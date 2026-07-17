"""Tests for text normalization and segmentation."""

from src.text_utils import clean_text, split_into_paragraphs, split_into_sentences


def test_clean_text_normalizes_whitespace_and_line_endings() -> None:
    text = " Hello   world\r\n\n\nTest "

    assert clean_text(text) == "Hello world\n\nTest"


def test_split_into_paragraphs() -> None:
    text = "Para 1\n\nPara 2\n\nPara 3"
    paragraphs = split_into_paragraphs(text)
    assert len(paragraphs) == 3


def test_split_into_paragraphs_returns_empty_fallback() -> None:
    assert split_into_paragraphs("   ") == [""]


def test_split_into_sentences_normalizes_and_splits_text() -> None:
    assert split_into_sentences("First.\n Second! Third?") == [
        "First.",
        "Second!",
        "Third?",
    ]


def test_split_into_sentences_handles_empty_text() -> None:
    assert split_into_sentences(" \n ") == []
