#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from fpms.modules.constants import PLATFORM, DISPLAY_TYPE
from fpms.modules.display import *
from fpms.modules.platform import *

# Initialize device to None
device = None

# Path to GPIO sysfs
gpio_sysfs_path = "/sys/class/gpio"

# Check if GPIO sysfs path exists and if the display type is ST7735
if os.path.exists(gpio_sysfs_path) and DISPLAY_TYPE == DISPLAY_TYPE_ST7735:
    # Use Waveshare's proprietary code to drive the ST7735 screen module
    from fpms.modules.screen.st7735 import ST7735
    device = ST7735()
else:
    # Default to Luma for driving the screen if not using a different implementation
    from fpms.modules.screen.luma import Luma
    device = Luma()

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
