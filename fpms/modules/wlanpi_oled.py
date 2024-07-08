#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fpms.modules.constants import PLATFORM, DISPLAY_TYPE
from fpms.modules.display import *
from fpms.modules.platform import *

device = None

if DISPLAY_TYPE == DISPLAY_TYPE_ST7735:
    # Let's use Waveshare's proprietary code to drive the ST7735 screen module
    from fpms.modules.screen.st7735 import ST7735
    device = ST7735()

# Default to Luma for driving the screen if not using a different implementation
if device is None:
    from fpms.modules.screen.luma import Luma
    device = Luma()

# Init function of the OLED
def init():
    device.init()

def drawImage(image):
    device.drawImage(image)

def clear():
    device.clear()

def sleep():
    device.sleep()

def wakeup():
    device.wakeup()
