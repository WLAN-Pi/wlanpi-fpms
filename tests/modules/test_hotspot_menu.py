import subprocess
from typing import Any

import pytest

from fpms.modules import modes
from fpms.modules.modes import hotspot_switcher, place_hotspot_menu


def _menu() -> list[dict[str, Any]]:
    return [
        {"name": "Network", "action": []},
        {"name": "Utils", "action": []},
        {"name": "Apps", "action": []},
        {"name": "System", "action": []},
    ]


def _names(menu: list[dict[str, Any]]) -> list[str]:
    return [item["name"] for item in menu]


def test_classic_menu_offers_hotspot_confirm(tmp_path):
    switcher = tmp_path / "hotspot_switcher"
    switcher.write_text("")
    called: list[str] = []

    def confirm() -> None:
        called.append("confirm")

    menu = _menu()
    place_hotspot_menu(menu, "classic", confirm, str(switcher))

    assert _names(menu) == ["Network", "Utils", "Modes", "Apps", "System"]
    hotspot = menu[2]["action"][0]
    assert hotspot["name"] == "Hotspot"
    assert hotspot["action"][0]["name"] == "Confirm"
    hotspot["action"][0]["action"]()
    assert called == ["confirm"]


def test_hotspot_menu_offers_classic_confirm(tmp_path):
    switcher = tmp_path / "hotspot_switcher"
    switcher.write_text("")
    called: list[str] = []

    def confirm() -> None:
        called.append("confirm")

    menu = _menu()
    place_hotspot_menu(menu, "hotspot", confirm, str(switcher))

    assert _names(menu) == ["Network", "Utils", "Mode", "Apps", "System"]
    classic = menu[2]["action"][0]
    assert classic["name"] == "Classic Mode"
    assert classic["action"][0]["name"] == "Confirm"
    classic["action"][0]["action"]()
    assert called == ["confirm"]


@pytest.mark.parametrize("mode", ["classic", "hotspot", "server", "bridge", "wiperf"])
def test_missing_switcher_hides_the_row(mode):
    menu = _menu()
    place_hotspot_menu(menu, mode, lambda: None, "/no/such/hotspot_switcher")
    assert _names(menu) == ["Network", "Utils", "Apps", "System"]


@pytest.mark.parametrize("mode", ["server", "bridge", "wiperf"])
def test_retired_modes_hide_the_row(mode, tmp_path):
    switcher = tmp_path / "hotspot_switcher"
    switcher.write_text("")
    menu = _menu()
    place_hotspot_menu(menu, mode, lambda: None, str(switcher))
    assert _names(menu) == ["Network", "Utils", "Apps", "System"]


class _Alert:
    def __init__(self, g_vars: dict[str, Any]) -> None:
        self.errors: list[str] = []
        self.popups: list[tuple[str, float]] = []

    def display_alert_error(
        self, g_vars: dict[str, Any], msg: str, title: str = "Error"
    ) -> None:
        self.errors.append(msg)

    def display_popup_alert(
        self, g_vars: dict[str, Any], msg: str, delay: float = 0.5
    ) -> None:
        self.popups.append((msg, delay))


def _switch(
    monkeypatch,
    mode: str,
    switcher: str,
    fail: bool = False,
) -> tuple[dict[str, Any], _Alert, list[list[str]]]:
    alerts: list[_Alert] = []

    def make_alert(g_vars: dict[str, Any]) -> _Alert:
        alert = _Alert(g_vars)
        alerts.append(alert)
        return alert

    launched: list[list[str]] = []

    def run(args: list[str], check: bool, capture_output: bool) -> None:
        launched.append(args)
        if fail:
            raise subprocess.CalledProcessError(1, args)

    monkeypatch.setattr(modes, "Alert", make_alert)
    monkeypatch.setattr(modes.subprocess, "run", run)
    monkeypatch.setattr(modes.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        modes.oled, "render_text", lambda *_a, **_k: None, raising=False
    )
    monkeypatch.setattr(modes.oled, "drawImage", lambda *_a, **_k: None, raising=False)
    g_vars = {
        "current_mode": mode,
        "reboot_image": "reboot",
        "shutdown_in_progress": False,
        "screen_cleared": True,
        "display_state": "page",
    }
    hotspot_switcher(g_vars, switcher)
    return g_vars, alerts[0], launched


def test_classic_confirm_runs_switcher_on(monkeypatch, tmp_path):
    switcher = tmp_path / "hotspot_switcher"
    switcher.write_text("")
    g_vars, alert, launched = _switch(monkeypatch, "classic", str(switcher))

    assert launched == [[str(switcher), "on"]]
    assert alert.popups == [("Switching to Hotspot mode...", 2)]
    assert alert.errors == ["Failed to enable Hotspot mode."]
    assert g_vars["shutdown_in_progress"] is False
    assert g_vars["display_state"] == "menu"
    assert g_vars["screen_cleared"] is False


def test_hotspot_confirm_runs_switcher_off(monkeypatch, tmp_path):
    switcher = tmp_path / "hotspot_switcher"
    switcher.write_text("")
    _g_vars, alert, launched = _switch(monkeypatch, "hotspot", str(switcher))

    assert launched == [[str(switcher), "off"]]
    assert alert.popups == [("Switching to Classic mode...", 2)]


def test_missing_switcher_does_not_launch(monkeypatch):
    g_vars, alert, launched = _switch(
        monkeypatch, "classic", "/no/such/hotspot_switcher"
    )

    assert launched == []
    assert alert.popups == []
    assert alert.errors == ["Hotspot mode not available."]
    assert g_vars["display_state"] == "page"
    assert g_vars["shutdown_in_progress"] is False


def test_retired_mode_does_not_launch(monkeypatch, tmp_path):
    switcher = tmp_path / "hotspot_switcher"
    switcher.write_text("")
    g_vars, alert, launched = _switch(monkeypatch, "server", str(switcher))

    assert launched == []
    assert alert.popups == []
    assert alert.errors == ["Unknown mode: server"]
    assert g_vars["display_state"] == "page"


def test_switcher_failure_reports_the_error(monkeypatch, tmp_path):
    switcher = tmp_path / "hotspot_switcher"
    switcher.write_text("")
    g_vars, alert, launched = _switch(monkeypatch, "classic", str(switcher), fail=True)

    assert launched == [[str(switcher), "on"]]
    assert alert.errors == ["Failed to enable Hotspot mode."]
    assert g_vars["display_state"] == "menu"
