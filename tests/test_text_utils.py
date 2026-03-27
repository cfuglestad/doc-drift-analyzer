from src.text_utils import clean_text, split_into_paragraphs


def test_clean_text_removes_extra_spaces():
    text = "Hello   world\n\n\nTest"
    cleaned = clean_text(text)
    assert "Hello world" in cleaned


def test_split_into_paragraphs():
    text = "Para 1\n\nPara 2\n\nPara 3"
    paragraphs = split_into_paragraphs(text)
    assert len(paragraphs) == 3
