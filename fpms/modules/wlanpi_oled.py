#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import os
import sys
import syslog

from PIL import Image

from fpms.modules.constants import (
    DISPLAY_TYPE,
    DISPLAY_TYPE_ST7735,
    DISPLAY_TYPE_VIRTUAL,
    DISPLAY_ORIENTATION_FLIPPED,
    DISPLAY_ORIENTATION_NORMAL
)
from fpms.modules.screen.st7735 import ST7735
from fpms.modules.screen.luma import Luma
from fpms.modules.screen.virtual import Virtual

device = None
orientation = DISPLAY_ORIENTATION_NORMAL

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
        msg = ("fpms: no display hardware detected (/dev/spidev* missing); "
               "using virtual display. Run 'fpms -e' for keyboard emulation "
               "and press 'g' to capture PNG screenshots.")
        syslog.openlog(ident="fpms", logoption=syslog.LOG_PID, facility=syslog.LOG_USER)
        syslog.syslog(syslog.LOG_WARNING, msg)
        syslog.closelog()
        print(msg, file=sys.stderr, flush=True)
        return Virtual()
    return ST7735() if DISPLAY_TYPE == DISPLAY_TYPE_ST7735 else Luma()

# Initialize the device
def init():
    global device
    if device is None:
        device = _select_device()
    device.init()

# Draw an image on the display
def drawImage(image):
    if orientation == DISPLAY_ORIENTATION_FLIPPED:
        device.drawImage(image.transpose(Image.Transpose.ROTATE_180))
    else:
        device.drawImage(image)

# Clear the display
def clear():
    device.clear()

# Put the display to sleep
def sleep():
    device.sleep()

# Wake up the display
def wakeup():
    device.wakeup()