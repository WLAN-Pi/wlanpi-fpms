import os.path
import subprocess
import time
from collections.abc import Callable
from typing import Any

import fpms.modules.wlanpi_oled as oled
from fpms.modules.constants import HOTSPOT_SWITCHER_FILE
from fpms.modules.pages.alert import Alert


def hotspot_switcher(
    g_vars: dict[str, Any], switcher_path: str = HOTSPOT_SWITCHER_FILE
) -> None:
    alert = Alert(g_vars)
    if not os.path.isfile(switcher_path):
        alert.display_alert_error(g_vars, "Hotspot mode not available.")
        g_vars["display_state"] = "page"
        return

    mode = g_vars["current_mode"]
    if mode == "classic":
        message = "Switching to Hotspot mode..."
        failure = "Failed to enable Hotspot mode."
        switch = "on"
    elif mode == "hotspot":
        message = "Switching to Classic mode..."
        failure = "Failed to switch to Classic mode."
        switch = "off"
    else:
        alert.display_alert_error(g_vars, f"Unknown mode: {mode}")
        g_vars["display_state"] = "page"
        return

    alert.display_popup_alert(g_vars, message, delay=2)
    g_vars["drawing_in_progress"] = True
    time.sleep(2)

    oled.render_text("Rebooting", ["Rebooting..."])
    oled.drawImage(g_vars["reboot_image"])

    try:
        subprocess.run([switcher_path, switch], check=True, capture_output=True)
        time.sleep(1)
    except (subprocess.CalledProcessError, OSError) as exc:
        print(exc)

    g_vars["drawing_in_progress"] = False
    g_vars["screen_cleared"] = False
    alert.display_alert_error(g_vars, failure)
    g_vars["display_state"] = "menu"


def place_hotspot_menu(
    menu: list[dict[str, Any]],
    current_mode: str,
    confirm: Callable[[], None],
    switcher_path: str = HOTSPOT_SWITCHER_FILE,
) -> None:
    if current_mode == "classic":
        label = "Modes"
        child = "Hotspot"
    elif current_mode == "hotspot":
        label = "Mode"
        child = "Classic Mode"
    else:
        return
    if not os.path.isfile(switcher_path):
        return
    item = {
        "name": label,
        "action": [{"name": child, "action": [{"name": "Confirm", "action": confirm}]}],
    }
    for index, entry in enumerate(menu):
        if entry["name"] == "Utils":
            menu.insert(index + 1, item)
            return
