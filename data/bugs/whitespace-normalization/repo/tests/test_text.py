import pytest
from text import normalize_whitespace


def test_collapses_internal_and_edge_whitespace():
    assert normalize_whitespace("  alpha\t beta\n gamma  ") == "alpha beta gamma"


def test_already_normalized_text_is_unchanged():
    assert normalize_whitespace("alpha beta") == "alpha beta"


def test_non_string_is_rejected():
    with pytest.raises(TypeError):
        normalize_whitespace(None)
