import importlib.util
import sys
import threading
import types
from pathlib import Path
from unittest.mock import Mock

import pytest


@pytest.fixture
def oled(monkeypatch):
    """Load wlanpi_oled with the screen backends stubbed out."""
    constants = types.ModuleType("fpms.modules.constants")
    constants.DISPLAY_ORIENTATION_FLIPPED = "flipped"
    constants.DISPLAY_ORIENTATION_NORMAL = "normal"
    constants.DISPLAY_TYPE = "st7735"
    constants.DISPLAY_TYPE_ST7735 = "st7735"
    constants.DISPLAY_TYPE_VIRTUAL = "virtual"
    monkeypatch.setitem(sys.modules, "fpms.modules.constants", constants)
    for name, cls in (("luma", "Luma"), ("st7735", "ST7735"), ("virtual", "Virtual")):
        mod = types.ModuleType(f"fpms.modules.screen.{name}")
        setattr(mod, cls, type(cls, (), {}))
        monkeypatch.setitem(sys.modules, f"fpms.modules.screen.{name}", mod)

    path = Path(__file__).parents[2] / "fpms" / "modules" / "wlanpi_oled.py"
    spec = importlib.util.spec_from_file_location("wlanpi_oled_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.device = Mock()
    return module


def test_writes_after_final_frame_are_dropped(oled):
    oled.final_frame("reboot")
    oled.drawImage("home")
    oled.clear()
    oled.sleep()
    oled.final_frame("shutdown")

    oled.device.drawImage.assert_called_once_with("reboot")
    oled.device.clear.assert_not_called()
    oled.device.sleep.assert_not_called()


def test_final_frame_waits_for_draw_in_progress(oled):
    order = []
    started = threading.Event()
    release = threading.Event()

    def slow_draw(image):
        if image == "home":
            started.set()
            release.wait(2)
        order.append(image)

    oled.device.drawImage.side_effect = slow_draw
    page = threading.Thread(target=oled.drawImage, args=("home",))
    page.start()
    started.wait(2)
    final = threading.Thread(target=oled.final_frame, args=("reboot",))
    final.start()
    release.set()
    page.join(2)
    final.join(2)

    assert order == ["home", "reboot"]


def test_final_frame_wakes_panel_after_drawing(oled):
    order = []
    oled.device.drawImage.side_effect = lambda image: order.append("draw")
    oled.device.wakeup.side_effect = lambda: order.append("wake")
    oled.sleep()

    oled.final_frame("reboot")
    oled.wakeup()

    assert order == ["draw", "wake"]
