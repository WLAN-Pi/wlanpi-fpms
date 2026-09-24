import subprocess

import pytest

from fpms.modules.constants import IP_FILE, IW_FILE
from fpms.modules.network import iw_dev_outputs, netns_cmd

ROOT_IW_DEV = "phy#0\n\tInterface wlan0\n\t\ttype managed\n"
NS_IW_DEV = "phy#1\n\tInterface wlan1\n\t\ttype monitor\n"


def fake_check_output(responses):
    """Return a subprocess.check_output fake keyed on the argv tuple."""

    def _check_output(cmd, **kwargs):
        assert "timeout" in kwargs
        result = responses[tuple(cmd)]
        if isinstance(result, Exception):
            raise result
        return result.encode()

    return _check_output


def test_netns_cmd_root_is_unchanged():
    assert netns_cmd("", [IW_FILE, "dev"]) == [IW_FILE, "dev"]


def test_netns_cmd_prefixes_named_netns():
    assert netns_cmd("ns1", [IW_FILE, "dev"]) == [
        IP_FILE,
        "netns",
        "exec",
        "ns1",
        IW_FILE,
        "dev",
    ]


def test_iw_dev_outputs_root_only(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "check_output",
        fake_check_output(
            {(IW_FILE, "dev"): ROOT_IW_DEV, (IP_FILE, "netns", "list"): ""}
        ),
    )

    assert iw_dev_outputs() == [("", ROOT_IW_DEV)]


def test_iw_dev_outputs_netns_list_failure_keeps_root(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "check_output",
        fake_check_output(
            {
                (IW_FILE, "dev"): ROOT_IW_DEV,
                (IP_FILE, "netns", "list"): FileNotFoundError(IP_FILE),
            }
        ),
    )

    assert iw_dev_outputs() == [("", ROOT_IW_DEV)]


def test_iw_dev_outputs_merges_named_netns(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "check_output",
        fake_check_output(
            {
                (IW_FILE, "dev"): ROOT_IW_DEV,
                (IP_FILE, "netns", "list"): "ns1 (id: 0)\n",
                (IP_FILE, "netns", "exec", "ns1", IW_FILE, "dev"): NS_IW_DEV,
            }
        ),
    )

    assert iw_dev_outputs() == [("", ROOT_IW_DEV), ("ns1", NS_IW_DEV)]


@pytest.mark.parametrize(
    "error",
    [
        subprocess.CalledProcessError(1, "ip"),
        subprocess.TimeoutExpired("ip", 5),
    ],
)
def test_iw_dev_outputs_skips_broken_netns(monkeypatch, error):
    monkeypatch.setattr(
        subprocess,
        "check_output",
        fake_check_output(
            {
                (IW_FILE, "dev"): ROOT_IW_DEV,
                (IP_FILE, "netns", "list"): "broken\nns1 (id: 1)\n",
                (IP_FILE, "netns", "exec", "broken", IW_FILE, "dev"): error,
                (IP_FILE, "netns", "exec", "ns1", IW_FILE, "dev"): NS_IW_DEV,
            }
        ),
    )

    assert iw_dev_outputs() == [("", ROOT_IW_DEV), ("ns1", NS_IW_DEV)]
