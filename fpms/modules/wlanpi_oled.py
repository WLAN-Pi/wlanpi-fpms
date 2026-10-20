#!/usr/bin/env python

import glob
import os
import sys
import syslog
import threading
from typing import Any

from PIL import Image

from fpms import boot_splash
from fpms.modules.constants import (
    DISPLAY_ORIENTATION_FLIPPED,
    DISPLAY_ORIENTATION_NORMAL,
    DISPLAY_TYPE,
    DISPLAY_TYPE_ST7735,
    DISPLAY_TYPE_VIRTUAL,
    GPIO_CHIP,
)
from fpms.modules.screen.luma import Luma
from fpms.modules.screen.st7735 import ST7735
from fpms.modules.screen.virtual import Virtual

device: Any = None
orientation = DISPLAY_ORIENTATION_NORMAL
_draw_lock = threading.Lock()
_frozen = False


def _has_spi_hardware():
    return bool(glob.glob("/dev/spidev*"))


def _select_device():
    """Pick the screen backend. Env override wins; fall back to virtual when
    no SPI hardware is present so fpms still runs on machines without a
    display (e.g. a VM), where it logs a warning instead of crashing."""
    if DISPLAY_TYPE == DISPLAY_TYPE_VIRTUAL:
        return Virtual()
    if os.environ.get("FPMS_DISPLAY") == DISPLAY_TYPE_VIRTUAL:
        return Virtual()
    if not _has_spi_hardware():
        msg = (
            "fpms: no ST7735/SSD1351 display hardware detected (/dev/spidev* "
            "missing); using virtual (text) display. The menu is shown as "
            "terminal text, which is only available without a physical "
            "display. Run 'fpms -e' for keyboard control and press 'g' to "
            "capture PNG screenshots."
        )
        syslog.openlog(ident="fpms", logoption=syslog.LOG_PID, facility=syslog.LOG_USER)
        syslog.syslog(syslog.LOG_WARNING, msg)
        syslog.closelog()
        print(msg, file=sys.stderr, flush=True)
        return Virtual()
    return ST7735() if DISPLAY_TYPE == DISPLAY_TYPE_ST7735 else Luma()


def select_device():
    global device
    if device is None:
        device = _select_device()


def init():
    select_device()
    device.init()


def _draw(image):
    device.drawImage(_oriented(image))


def drawImage(image):
    with _draw_lock:
        if not _frozen:
            _draw(image)


def _oriented(image):
    if orientation == DISPLAY_ORIENTATION_FLIPPED:
        return image.transpose(Image.Transpose.ROTATE_180)
    return image


def save_boot_splash(image, path=boot_splash.SPLASH_FILE):
    """Store a frame fpms-splash can draw, for this panel and orientation."""
    if isinstance(device, ST7735):
        panel = boot_splash.PANEL_ST7735
    elif isinstance(device, Luma):
        panel = boot_splash.PANEL_SSD1351
    else:
        return
    frame = boot_splash.rgb565(_oriented(image).resize((128, 128)))
    boot_splash.save(panel, GPIO_CHIP, frame, path)


def final_frame(image):
    """Draw the shutdown/reboot image and ignore every later write."""
    global _frozen
    with _draw_lock:
        if not _frozen:
            _draw(image)
            _frozen = True
            device.wakeup()


def render_text(title, lines):
    if isinstance(device, Virtual):
        device.render_text(title, lines)


def set_hints(hints):
    if isinstance(device, Virtual):
        device.set_hints(hints)


def clear():
    with _draw_lock:
        if not _frozen:
            device.clear()


def sleep():
    with _draw_lock:
        if not _frozen:
            device.sleep()


def wakeup():
    with _draw_lock:
        if not _frozen:
            device.wakeup()
