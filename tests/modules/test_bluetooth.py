import json
import subprocess

import pytest

from fpms.modules import bluetooth
from fpms.modules.constants import BT_ADAPTER_FILE


def raising(exc):
    def _check_output(cmd, **kwargs):
        raise exc

    return _check_output


def test_bt_adapter_uses_wlanpi_bt_adapter(monkeypatch):
    calls = []

    def check_output(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return b"hci1\n"

    monkeypatch.setattr(subprocess, "check_output", check_output)

    assert bluetooth.bt_adapter() == "hci1"
    assert calls[0][0] == [BT_ADAPTER_FILE]
    assert calls[0][1]["timeout"] == 2


def test_bt_adapter_falls_back_to_hci0_only_without_the_selector(monkeypatch):
    monkeypatch.setattr(
        subprocess, "check_output", raising(FileNotFoundError(BT_ADAPTER_FILE))
    )

    assert bluetooth.bt_adapter() == "hci0"


@pytest.mark.parametrize(
    "check_output",
    [
        raising(PermissionError(BT_ADAPTER_FILE)),
        raising(subprocess.CalledProcessError(1, [BT_ADAPTER_FILE])),
        raising(subprocess.TimeoutExpired([BT_ADAPTER_FILE], 2)),
        lambda cmd, **kwargs: b"",
        lambda cmd, **kwargs: b"hci1; reboot\n",
    ],
    ids=["not-executable", "exit-1", "timeout", "empty", "not-an-adapter"],
)
def test_bt_adapter_failure_means_no_adapter(monkeypatch, check_output):
    monkeypatch.setattr(subprocess, "check_output", check_output)

    assert bluetooth.bt_adapter() is None


def test_no_adapter_is_not_present_and_never_pairs(monkeypatch):
    calls = []
    monkeypatch.setattr(bluetooth, "bt_adapter", lambda: None)
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: calls.append(cmd))
    bt = bluetooth.Bluetooth({})
    bt.alert_obj = Alerts()

    bt.bluetooth_pair({"result_cache": False})

    assert calls == []
    assert bt.alert_obj.shown == [("error", "Bluetooth adapter not found.")]


# BlueZ's device objects: (Paired, Address, Alias). A dongle on hci0 and the
# chosen adapter hci1 each have a paired device; hci1 also knows an unpaired one.
DEVICES = {
    "/org/bluez/hci0/dev_00_00_00_00_00_01": (
        True,
        "00:00:00:00:00:01",
        "Dongle phone",
    ),
    "/org/bluez/hci1/dev_00_00_00_00_00_02": (True, "00:00:00:00:00:02", "Phone"),
    "/org/bluez/hci1/dev_00_00_00_00_00_03": (False, "00:00:00:00:00:03", "Nearby"),
}


class Alerts:
    """Records the alerts a page shows."""

    def __init__(self):
        self.shown = []

    def display_popup_alert(self, g_vars, msg, **kwargs):
        self.shown.append(("popup", msg))

    def display_alert_info(self, g_vars, msg, **kwargs):
        self.shown.append(("info", msg))

    def display_alert_error(self, g_vars, msg, **kwargs):
        self.shown.append(("error", msg))


@pytest.fixture
def bt(monkeypatch):
    """
    A Bluetooth on hci1 with BlueZ faked; records every command run. Set
    state["query_fails"] or state["remove_fails"] to make busctl fail, or
    state["remove_ignored"] to leave removed devices paired. state["relist"]
    replaces every BlueZ listing after the first: an exception, or the paths.
    """
    state = {"objects": dict(DEVICES), "calls": [], "clock": 0.0}

    def run(cmd, **kwargs):
        state["calls"].append(cmd)
        if isinstance(cmd, list) and "RemoveDevice" in cmd:
            state["remove_kwargs"] = kwargs
            if state.get("remove_fails"):
                if kwargs.get("check"):
                    raise subprocess.CalledProcessError(1, cmd)
                return subprocess.CompletedProcess(cmd, 1)
            if not state.get("remove_ignored"):
                state["objects"].pop(cmd[-1], None)
        return subprocess.CompletedProcess(cmd, 0)

    def check_output(cmd, **kwargs):
        state["calls"].append(cmd)
        if "busctl" not in cmd:
            return b""
        if state.get("query_fails"):
            raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])
        if cmd == ["busctl", "--system", "tree", "--list", "org.bluez"]:
            state["listings"] = state.get("listings", 0) + 1
            if state["listings"] > 1 and "relist" in state:
                if isinstance(state["relist"], Exception):
                    raise state["relist"]
                return "\n".join(state["relist"]).encode()
            # Includes the objects above devices and a device's child object.
            paths = ["/", "/org", "/org/bluez", "/org/bluez/hci0", "/org/bluez/hci1"]
            paths += [*state["objects"], "/org/bluez/hci1/dev_00_00_00_00_00_02/fd0"]
            # Devices BlueZ drops right after this listing.
            paths += state.pop("dropped", [])
            return "\n".join(paths).encode()
        assert cmd[:4] == ["busctl", "--system", "--json=short", "get-property"]
        assert cmd[4] == "org.bluez"
        assert cmd[6:] == ["org.bluez.Device1", "Paired", "Address", "Alias"]
        if cmd[5] not in state["objects"] or cmd[5] in state.get("unreadable", ()):
            raise subprocess.CalledProcessError(1, cmd)
        values = zip(("b", "s", "s"), state["objects"][cmd[5]], strict=True)
        return "\n".join(json.dumps({"type": t, "data": v}) for t, v in values).encode()

    def sleep(seconds):
        state["clock"] += seconds

    monkeypatch.setattr(bluetooth, "bt_adapter", lambda: "hci1")
    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr(subprocess, "check_output", check_output)
    monkeypatch.setattr(bluetooth.time, "sleep", sleep)
    monkeypatch.setattr(bluetooth.time, "monotonic", lambda: state["clock"])
    obj = bluetooth.Bluetooth({})
    obj.alert_obj = Alerts()
    obj.calls = state["calls"]
    obj.state = state
    return obj


def test_paired_devices_lists_only_the_chosen_adapter(bt):
    assert bt.bluetooth_paired_devices() == {"00:00:00:00:00:02": "Phone"}


def test_paired_devices_reads_only_the_chosen_adapters_devices(bt):
    assert bt.paired_device_objects() == {
        "/org/bluez/hci1/dev_00_00_00_00_00_02": ("00:00:00:00:00:02", "Phone")
    }
    assert [cmd[5] for cmd in bt.calls if "get-property" in cmd] == [
        "/org/bluez/hci1/dev_00_00_00_00_00_02",
        "/org/bluez/hci1/dev_00_00_00_00_00_03",
    ]


def test_paired_devices_skips_a_device_dropped_since_the_listing(bt):
    bt.state["dropped"] = ["/org/bluez/hci1/dev_00_00_00_00_00_09"]

    assert bt.paired_device_objects() == {
        "/org/bluez/hci1/dev_00_00_00_00_00_02": ("00:00:00:00:00:02", "Phone")
    }
    assert len([cmd for cmd in bt.calls if "tree" in cmd]) == 2


@pytest.mark.parametrize(
    "relist",
    [subprocess.CalledProcessError(1, "busctl"), ["/", "/org", "/org/bluez"]],
    ids=["relist-fails", "adapter-gone"],
)
def test_pair_fails_if_a_read_failure_cannot_be_explained(bt, relist):
    bt.state["dropped"] = ["/org/bluez/hci1/dev_00_00_00_00_00_09"]
    bt.state["relist"] = relist
    g_vars = {"result_cache": False}

    with pytest.raises((subprocess.CalledProcessError, RuntimeError)):
        bt.paired_device_objects()
    bt.state["dropped"] = ["/org/bluez/hci1/dev_00_00_00_00_00_09"]
    bt.state["listings"] = 0
    bt.bluetooth_pair(g_vars)
    bt.bluetooth_pair(g_vars)

    assert ["systemctl", "start", "bt-timedpair"] not in bt.calls
    assert bt.alert_obj.shown[-1] == ("error", "Failed to remove paired devices.")


def test_paired_devices_raises_if_bluez_has_not_registered_the_adapter(bt):
    bt.adapter = "hci2"

    with pytest.raises(RuntimeError):
        bt.paired_device_objects()


def test_paired_devices_raises_if_a_listed_device_cannot_be_read(bt):
    bt.state["unreadable"] = {"/org/bluez/hci1/dev_00_00_00_00_00_03"}

    with pytest.raises(subprocess.CalledProcessError):
        bt.paired_device_objects()


def test_paired_devices_queries_have_a_timeout(bt, monkeypatch):
    timeouts = []
    check_output = subprocess.check_output

    def timed(cmd, **kwargs):
        timeouts.append(kwargs["timeout"])
        return check_output(cmd, **kwargs)

    monkeypatch.setattr(subprocess, "check_output", timed)

    bt.paired_device_objects()

    assert timeouts == [10, 10, 10]


def test_pair_removes_devices_from_the_chosen_adapter(bt):
    g_vars = {"result_cache": False}

    bt.bluetooth_pair(g_vars)

    removals = [cmd for cmd in bt.calls if "RemoveDevice" in cmd]
    assert removals == [
        [
            "busctl",
            "--system",
            "call",
            "org.bluez",
            "/org/bluez/hci1",
            "org.bluez.Adapter1",
            "RemoveDevice",
            "o",
            "/org/bluez/hci1/dev_00_00_00_00_00_02",
        ]
    ]
    assert bt.state["remove_kwargs"]["timeout"] == 10
    assert bt.bluetooth_paired_devices() is None
    assert g_vars["result_cache"] is True

    bt.bluetooth_pair(g_vars)

    assert ["systemctl", "start", "bt-timedpair"] in bt.calls
    assert bt.alert_obj.shown[-1][0] == "info"


def test_pair_removes_a_device_by_its_object_path(bt):
    # A device with a random address keeps the object path BlueZ first gave it.
    bt.state["objects"] = {
        "/org/bluez/hci1/dev_4A_00_00_00_00_09": (True, "7B:00:00:00:00:09", "Phone")
    }

    bt.bluetooth_pair({"result_cache": False})

    assert [cmd[-1] for cmd in bt.calls if "RemoveDevice" in cmd] == [
        "/org/bluez/hci1/dev_4A_00_00_00_00_09"
    ]
    assert bt.state["objects"] == {}


@pytest.mark.parametrize("failure", ["query_fails", "remove_fails", "remove_ignored"])
def test_pair_never_opens_the_window_if_a_pairing_is_not_removed(bt, failure):
    bt.state[failure] = True
    g_vars = {"result_cache": False}

    for _ in range(3):
        bt.bluetooth_pair(g_vars)

    assert ["systemctl", "start", "bt-timedpair"] not in bt.calls
    assert bt.alert_obj.shown[-1] == ("error", "Failed to remove paired devices.")
    assert g_vars["disable_keys"] is False
    if failure == "remove_ignored":
        assert bt.state["clock"] <= 32
    if failure == "remove_fails":
        assert len([cmd for cmd in bt.calls if "RemoveDevice" in cmd]) == 1


def test_pair_does_not_open_the_window_if_paired_devices_cannot_be_read(bt):
    g_vars = {"result_cache": False}
    bt.bluetooth_pair(g_vars)
    bt.calls.clear()
    bt.state["query_fails"] = True

    bt.bluetooth_pair(g_vars)

    assert ["systemctl", "start", "bt-timedpair"] not in bt.calls
    assert bt.alert_obj.shown[-1] == ("error", "Failed to read paired devices.")


def test_pair_reports_a_new_pairing(bt):
    g_vars = {"result_cache": False}
    bt.bluetooth_pair(g_vars)
    bt.state["objects"]["/org/bluez/hci1/dev_00_00_00_00_00_04"] = (
        True,
        "00:00:00:00:00:04",
        "New phone",
    )

    bt.bluetooth_pair(g_vars)

    assert bt.alert_obj.shown[-1] == ("info", "Paired to New phone")


def test_adapter_commands_use_the_chosen_adapter(bt):
    bt.bluetooth_present()
    bt.bluetooth_power()

    assert bt.calls == ["hciconfig | grep hci1", r"hciconfig hci1 | grep -E '^\s+UP'"]
