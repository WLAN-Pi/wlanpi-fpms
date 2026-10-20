import pytest

from fpms.modules.pages import homepage

UP = "Speed: 1000Mb/s\nDuplex: Full\nLink detected: yes\n"


@pytest.mark.parametrize(
    "ethtool,expected",
    [
        (UP, "1000Mb/s Full"),
        ("Speed: 1000Mb/s\nDuplex: Full\nLink detected: no\n", "Link down"),
        ("Link detected: no\n", "Link down"),
        ("Link detected: yes\n", None),
        ("Speed: 100Mb/s\nDuplex: Half\n", "100Mb/s Half"),
    ],
)
def test_if_link_status(monkeypatch, ethtool, expected):
    page = homepage.HomePage.__new__(homepage.HomePage)
    monkeypatch.setattr(page, "if_wireless", lambda _: False)
    monkeypatch.setattr(
        homepage.subprocess, "check_output", lambda *a, **k: ethtool.encode()
    )
    assert page.if_link_status("eth0") == expected
