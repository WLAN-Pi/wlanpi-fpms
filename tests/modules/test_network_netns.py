import subprocess

import pytest

from fpms.modules.constants import IFCONFIG_FILE, IP_FILE, IW_FILE
from fpms.modules.network import (
    interface_lines,
    iw_dev_outputs,
    netns_cmd,
    netns_outputs,
)

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


IFCONFIG = """\
eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 192.168.6.59  netmask 255.255.255.0  broadcast 192.168.6.255
        RX packets 10  bytes 100 (100.0 B)
lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536
        inet 127.0.0.1  netmask 255.0.0.0
        RX packets 1  bytes 10 (10.0 B)
"""

NS_IFCONFIG = """\
lo: flags=8<LOOPBACK>  mtu 65536
        RX packets 0  bytes 0 (0.0 B)
wlan2: flags=4098<BROADCAST,MULTICAST>  mtu 1500
        RX packets 0  bytes 0 (0.0 B)
"""


def test_interface_lines_root_keeps_lo(monkeypatch):
    assert interface_lines("", IFCONFIG) == ["▲ e0:192.168.6.59", "▲ lo:127.0.0.1"]


def test_interface_lines_netns_skips_lo_and_checks_monitor_inside(monkeypatch):
    calls = []

    def _check_output(cmd, **kwargs):
        calls.append(cmd)
        return b"Interface wlan2\n\ttype monitor\n"

    monkeypatch.setattr(subprocess, "check_output", _check_output)

    assert interface_lines("ns1", NS_IFCONFIG) == ["▽ w2:Monitor"]
    assert calls == [[IP_FILE, "netns", "exec", "ns1", IW_FILE, "wlan2", "info"]]


def test_netns_outputs_runs_cmd_in_each_netns(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "check_output",
        fake_check_output(
            {
                (IFCONFIG_FILE, "-a"): IFCONFIG,
                (IP_FILE, "netns", "list"): "ns1 (id: 0)\n",
                (IP_FILE, "netns", "exec", "ns1", IFCONFIG_FILE, "-a"): NS_IFCONFIG,
            }
        ),
    )

    assert netns_outputs([IFCONFIG_FILE, "-a"]) == [
        ("", IFCONFIG),
        ("ns1", NS_IFCONFIG),
    ]


def test_netns_outputs_root_failure_raises(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "check_output",
        fake_check_output({(IFCONFIG_FILE, "-a"): FileNotFoundError(IFCONFIG_FILE)}),
    )

    with pytest.raises(FileNotFoundError):
        netns_outputs([IFCONFIG_FILE, "-a"])


class _Table:
    def __init__(self):
        self.lines = None

    def display_list_as_paged_table(self, g_vars, lines, title=""):
        self.lines = lines


def _show_interfaces(monkeypatch, outputs):
    import fpms.modules.network as network

    monkeypatch.setattr(network, "netns_outputs", lambda cmd: outputs)
    monkeypatch.setattr(
        subprocess, "check_output", lambda cmd, **kw: b"\ttype monitor\n"
    )
    obj = network.Network.__new__(network.Network)
    obj.paged_table_obj = _Table()
    obj.show_interfaces({"display_state": "page"})
    return obj.paged_table_obj.lines


def test_show_interfaces_groups_named_netns_under_heading(monkeypatch):
    assert _show_interfaces(monkeypatch, [("", IFCONFIG), ("ns1", NS_IFCONFIG)]) == [
        "▲ e0:192.168.6.59",
        "▲ lo:127.0.0.1",
        "[ns1]",
        "▽ w2:Monitor",
    ]


def test_show_interfaces_omits_heading_for_loopback_only_netns(monkeypatch):
    lo_only = "lo: flags=8<LOOPBACK>  mtu 65536\n        RX packets 0\n"
    assert _show_interfaces(monkeypatch, [("", IFCONFIG), ("ns1", lo_only)]) == [
        "▲ e0:192.168.6.59",
        "▲ lo:127.0.0.1",
    ]
