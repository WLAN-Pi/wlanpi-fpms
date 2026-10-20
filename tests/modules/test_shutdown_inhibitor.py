import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import Mock

import pytest


@pytest.fixture
def shutdown_module(monkeypatch):
    """Load the shutdown handlers with no Pi hardware or system bus."""
    module_names = (
        "dbus",
        "dbus.mainloop",
        "dbus.mainloop.glib",
        "gi",
        "gi.repository",
        "gpiod",
        "gpiod.line",
        "fpms.modules.wlanpi_oled",
        "fpms.modules.apps.kismet",
        "fpms.modules.apps.profiler",
        "fpms.modules.apps.scanner",
        "fpms.modules.battery",
        "fpms.modules.bluetooth",
        "fpms.modules.cloud_tests",
        "fpms.modules.constants",
        "fpms.modules.env_utils",
        "fpms.modules.nav.buttons",
        "fpms.modules.network",
        "fpms.modules.pages.homepage",
        "fpms.modules.pages.page",
        "fpms.modules.reg_domain",
        "fpms.modules.system",
        "fpms.modules.time_zone",
        "fpms.modules.utils",
    )
    modules = {name: types.ModuleType(name) for name in module_names}
    for name, module in modules.items():
        if name.startswith("fpms."):
            module.__getattr__ = lambda attr: Mock()
        monkeypatch.setitem(sys.modules, name, module)
    modules["gpiod.line"].Bias = Mock()
    modules["gpiod.line"].Edge = Mock()
    modules["fpms.modules.constants"].DISPLAY_ORIENTATION_NORMAL = 0
    modules["fpms.modules.constants"].PAGE_SLEEP = 10
    modules["dbus"].mainloop = modules["dbus.mainloop"]
    modules["dbus.mainloop"].glib = modules["dbus.mainloop.glib"]
    modules["dbus.mainloop.glib"].DBusGMainLoop = Mock()
    bus = Mock()
    login1 = Mock()
    login1.Inhibit.return_value.take.return_value = 123
    modules["dbus"].SystemBus = Mock(return_value=bus)
    modules["dbus"].Interface = Mock(return_value=login1)
    loop = Mock()
    modules["gi.repository"].GLib = types.SimpleNamespace(
        MainLoop=Mock(return_value=loop)
    )
    monkeypatch.setattr("os.geteuid", lambda: 0)
    path = Path(__file__).parents[2] / "fpms" / "fpms.py"
    spec = importlib.util.spec_from_file_location("fpms._shutdown_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.log_to_syslog = Mock()
    module.g_vars["shutdown_image"] = "shutdown"
    module.g_vars["reboot_image"] = "reboot"
    events = []
    module.oled.final_frame = Mock(side_effect=lambda image: events.append(image))
    module.os = types.SimpleNamespace(
        close=Mock(side_effect=lambda fd: events.append(fd))
    )
    return module, login1, loop, events


@pytest.mark.parametrize("shutdown", [False, True])
def test_shutdown_releases_inhibitor_after_drawing(shutdown_module, shutdown):
    module, login1, loop, events = shutdown_module
    loop.run.side_effect = lambda: module.handle_reboot_or_shutdown(shutdown)

    module.run_dbus_loop()

    login1.Inhibit.assert_called_once_with(
        "shutdown", "fpms", "Delaying shutdown", "delay"
    )
    login1.Inhibit.return_value.take.assert_called_once_with()
    assert events == ["shutdown" if shutdown else "reboot", 123]


def test_already_drawn_shutdown_releases_inhibitor(shutdown_module):
    module, _, loop, events = shutdown_module
    module.g_vars["shutdown_in_progress"] = True
    loop.run.side_effect = module.handle_reboot_or_shutdown

    module.run_dbus_loop()

    assert events == [123]


def test_duplicate_shutdown_signals_release_inhibitor_once(shutdown_module):
    module, _, loop, events = shutdown_module

    def notifications():
        module.handle_prepare_for_shutdown(True)
        module.handle_jobnew("reboot.target")
        module.handle_prepare_for_shutdown(True)

    loop.run.side_effect = notifications

    module.run_dbus_loop()

    assert events == ["reboot", 123]


def test_failed_shutdown_drawing_releases_inhibitor(shutdown_module):
    module, _, loop, events = shutdown_module
    module.oled.final_frame.side_effect = RuntimeError("display unavailable")
    loop.run.side_effect = module.handle_reboot_or_shutdown

    with pytest.raises(RuntimeError, match="display unavailable"):
        module.run_dbus_loop()

    assert events == [123]


def test_dbus_loop_exit_releases_inhibitor(shutdown_module):
    module, _, _, events = shutdown_module

    module.run_dbus_loop()

    assert events == [123]
