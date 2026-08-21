"""Smoke tests for the Streamlit composition layer."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

_APP_PATH = Path(__file__).resolve().parent.parent / "app" / "streamlit_app.py"


def test_app_starts_with_lexical_backend_and_legacy_threshold() -> None:
    app = AppTest.from_file(str(_APP_PATH)).run(timeout=10)

    assert not app.exception
    assert app.selectbox[0].value == "lexical"
    assert app.slider[0].value == 0.35


def test_app_uses_backend_specific_threshold_control() -> None:
    app = AppTest.from_file(str(_APP_PATH)).run(timeout=10)

    app.selectbox[0].set_value("semantic").run(timeout=10)

    assert app.slider[0].value == 0.65
