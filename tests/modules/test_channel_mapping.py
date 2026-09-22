import pytest

from fpms.modules.apps.scanner import Scanner
from fpms.modules.network import Network

# `channel_lookup` (network.py) and `freq_to_channel` (scanner.py) are
# duplicated implementations. These tests pin the expected values and guard
# against the two copies drifting apart.
FREQUENCIES = [
    2484,
    2412,
    2437,
    2472,
    5180,
    5200,
    5745,
    5825,
    5955,
    6115,
    7115,
    0,
    1000,
    8000,
]


@pytest.mark.parametrize("freq", FREQUENCIES)
def test_implementations_agree(freq):
    assert Network.channel_lookup(None, freq) == Scanner.freq_to_channel(None, freq)


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
    assert Network.channel_lookup(None, freq) == expected
