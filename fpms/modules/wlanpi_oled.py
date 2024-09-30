#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from PIL import Image

from fpms.modules.constants import (
    DISPLAY_TYPE,
    DISPLAY_TYPE_ST7735,
    DISPLAY_ORIENTATION_FLIPPED,
    DISPLAY_ORIENTATION_NORMAL
)
from fpms.modules.screen.st7735 import ST7735
from fpms.modules.screen.luma import Luma

# Initialize device based on the display type
device = ST7735() if DISPLAY_TYPE == DISPLAY_TYPE_ST7735 else Luma()
orientation = DISPLAY_ORIENTATION_NORMAL

# Initialize the device
def init():
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
