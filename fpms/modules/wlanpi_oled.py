#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from fpms.modules.constants import DISPLAY_TYPE, DISPLAY_TYPE_ST7735
from fpms.modules.screen.st7735 import ST7735
from fpms.modules.screen.luma import Luma

# Initialize device based on the display type
device = ST7735() if DISPLAY_TYPE == DISPLAY_TYPE_ST7735 else Luma()

# Initialize the device
def init():
    device.init()

# Draw an image on the display
def drawImage(image):
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
