"""Tests for the typed pipeline consumed by the Streamlit application."""

from src.alignment import SectionAligner
from src.diffing import classify_change, word_diff_html
from src.sectioning import extract_sections
from src.similarity import LexicalSimilarityBackend
from src.summarization import RuleBasedChangeSummarizer
from src.text_utils import clean_text


def test_streamlit_facing_pipeline_consumes_typed_results() -> None:
    old_sections = extract_sections(clean_text("POLICY\nKeep records."))
    new_sections = extract_sections(clean_text("POLICY\nKeep all records."))
    alignments = SectionAligner(LexicalSimilarityBackend()).align(
        old_sections, new_sections, threshold=0.35
    )

    summary = RuleBasedChangeSummarizer().summarize(alignments)
    alignment = alignments[0]
    label = classify_change(alignment.old_content, alignment.new_content, alignment.similarity)
    inline_diff = word_diff_html(alignment.old_content, alignment.new_content)

    assert label == "Edited (minor)"
    assert summary.minor_edits == 1
    assert summary.bullets == ("Minor edits in section: POLICY",)
    assert "background-color:#d1fae5" in inline_diff
