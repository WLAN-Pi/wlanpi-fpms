import pytest

from fpms.modules.network import freq_to_channel


@pytest.mark.parametrize(
    "freq,expected",
    [
        (2484, 14),
        (2412, 1),
        (2437, 6),
        (5180, 36),
        (5200, 40),
        (5955, 1),
        (1000, None),
        (8000, None),
    ],
)
def test_known_channels(freq, expected):
    assert freq_to_channel(freq) == expected
