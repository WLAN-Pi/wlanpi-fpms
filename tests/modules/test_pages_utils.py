from fpms.modules.pages.utils import StringFormatter


def test_justify_pads_after_colon():
    assert StringFormatter().justify("Foo:bar", width=10) == "Foo:   bar"


def test_justify_returns_text_without_colon():
    assert StringFormatter().justify("nocolon", width=10) == "nocolon"


def test_justify_returns_text_when_already_wide_enough():
    assert StringFormatter().justify("Foo:1234567890", width=5) == "Foo:1234567890"


def test_split_wraps_long_lines():
    assert StringFormatter().split(["abcdefghij"], length=4) == ["abcd", "efgh", "ij"]


def test_split_keeps_short_lines():
    assert StringFormatter().split(["ab", "cdef"], length=4) == ["ab", "cdef"]
