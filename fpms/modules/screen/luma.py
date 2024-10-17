#!/usr/bin/env python
# -*- coding: utf-8 -*-

from luma.core import cmdline, error
from PIL import Image
import sys
import logging
from fpms.modules.constants import PLATFORM, DISPLAY_TYPE
from fpms.modules.display import *
from fpms.modules.platform import *
from fpms.modules.screen.screen import AbstractScreen

# set possible vars to None
I2C_PORT = None
SPI_BUS_SPEED = None
I2C_ADDRESS = None
INTERFACE_TYPE = None
WIDTH = None
HEIGHT = None
COLOR_ORDER_BGR = True
GPIO_DATA_COMMAND = None
GPIO_RESET = None
GPIO_BACKLIGHT = None
GPIO_CS = None
BACKLIGHT_ACTIVE = None
H_OFFSET = None
V_OFFSET = None

if DISPLAY_TYPE == DISPLAY_TYPE_SSD1351:
    # ssd1351 128 x 128
    INTERFACE_TYPE = "spi"
    WIDTH = "128"
    HEIGHT = "128"
elif DISPLAY_TYPE == DISPLAY_TYPE_ST7735:
    # 128x128 1.44 in LCD Display HAT
    INTERFACE_TYPE = "gpio_cs_spi"
    SPI_BUS_SPEED = "2000000"
    WIDTH = "128"
    HEIGHT = "128"
    GPIO_DATA_COMMAND = "25"
    GPIO_RESET = "27"
    GPIO_BACKLIGHT = "24"
    GPIO_CS = "8"
    BACKLIGHT_ACTIVE = "high"
    H_OFFSET = "1"
    V_OFFSET = "2"
elif DISPLAY_TYPE == DISPLAY_TYPE_ST7789:
    # 240x240 1.3 in LCD Display HAT
    INTERFACE_TYPE = "gpio_cs_spi"
    SPI_BUS_SPEED = "52000000"
    WIDTH = "240"
    HEIGHT = "240"
    GPIO_DATA_COMMAND = "25"
    GPIO_RESET = "27"
    GPIO_BACKLIGHT = "24"
    GPIO_CS = "8"
    BACKLIGHT_ACTIVE = "high"

'''
### This code is borrowed from https://github.com/rm-hull/luma.examples/blob/master/examples/demo_opts.py
(MIT License)
'''
# logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)-15s - %(message)s'
)
# ignore PIL debug messages
logging.getLogger('PIL').setLevel(logging.ERROR)

DISPLAY_WIDTH = int(WIDTH)
DISPLAY_HEIGHT = int(HEIGHT)

def display_settings(device, args):
    """
    Display a short summary of the settings.

    :rtype: str
    """
    iface = ''
    display_types = cmdline.get_display_types()
    if args.display not in display_types['emulator']:
        iface = 'Interface: {}\n'.format(args.interface)

    lib_name = cmdline.get_library_for_display_type(args.display)
    if lib_name is not None:
        lib_version = cmdline.get_library_version(lib_name)
    else:
        lib_name = lib_version = 'unknown'

    import luma.core
    version = 'luma.{} {} (luma.core {})'.format(
        lib_name, lib_version, luma.core.__version__)

    return '{0}\nVersion: {1}\nDisplay: {2}\n{3}Dimensions: {4} x {5}\nMode: {6}\n{7}'.format(
        '-' * 50, version, args.display, iface, device.width, device.height, device.mode, '-' * 50)


def get_device(actual_args=None):
    """
    Create device from command-line arguments and return it.
    """
    if actual_args is None:
        actual_args = sys.argv[1:]
    parser = cmdline.create_parser(description='luma.examples arguments')
    args = parser.parse_args(actual_args)

    if args.config:
        # load config from file
        config = cmdline.load_config(args.config)
        args = parser.parse_args(config + actual_args)

    # create device
    try:
        device = cmdline.create_device(args)
        print(display_settings(device, args))
        return device

    except error.Error as e:
        parser.error(e)
        return None

'''
### End of borrowed code
'''

actual_args = []

if DISPLAY_TYPE:
    actual_args.append("-d")
    actual_args.append(DISPLAY_TYPE)

if INTERFACE_TYPE:
    actual_args.append("--interface")
    actual_args.append(INTERFACE_TYPE)

if WIDTH:
    actual_args.append("--width")
    actual_args.append(WIDTH)

if HEIGHT:
    actual_args.append("--height")
    actual_args.append(HEIGHT)

if I2C_PORT:
    actual_args.append("--i2c-port")
    actual_args.append(I2C_PORT)

if SPI_BUS_SPEED:
    actual_args.append("--spi-bus-speed")
    actual_args.append(SPI_BUS_SPEED)

if COLOR_ORDER_BGR:
    actual_args.append("--bgr")

if GPIO_DATA_COMMAND:
    actual_args.append("--gpio-data-command")
    actual_args.append(GPIO_DATA_COMMAND)

if GPIO_RESET:
    actual_args.append("--gpio-reset")
    actual_args.append(GPIO_RESET)

if GPIO_BACKLIGHT:
    actual_args.append("--gpio-backlight")
    actual_args.append(GPIO_BACKLIGHT)

if GPIO_CS:
    actual_args.append("--gpio-chip-select")
    actual_args.append(GPIO_CS)

if BACKLIGHT_ACTIVE:
    actual_args.append("--backlight-active")
    actual_args.append(BACKLIGHT_ACTIVE)

if H_OFFSET:
    actual_args.append("--h-offset")
    actual_args.append(H_OFFSET)

if V_OFFSET:
    actual_args.append("--v-offset")
    actual_args.append(V_OFFSET)

class Luma(AbstractScreen):

    def init(self):
        self.device = get_device(actual_args=actual_args)
        if PLATFORM == PLATFORM_PRO:
            # Reduce the contrast to also help reduce the noise
            # that's being produced by the display for some reason
            self.device.contrast(128)
        return True

    def drawImage(self, image):
        img = image.convert(self.device.mode)
        width, height = img.size
        if DISPLAY_WIDTH != width or DISPLAY_HEIGHT != height:
            img = img.resize((DISPLAY_WIDTH, DISPLAY_HEIGHT), Image.LANCZOS)

        self.device.display(img)

    def clear(self):
        self.device.clear()

    def sleep(self):
        self.device.clear()
        if PLATFORM != PLATFORM_PRO:
            self.device.backlight(False)

    def wakeup(self):
        if PLATFORM != PLATFORM_PRO:
            self.device.backlight(True)
