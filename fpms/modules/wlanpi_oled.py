#!/usr/bin/env python
# -*- coding: utf-8 -*-

from luma.core import cmdline, error
from PIL import Image
import sys
import logging
from fpms.modules.constants import PLATFORM

# set possible vars to None
DISPLAY_TYPE = None
I2C_PORT = None
I2C_ADDRESS = None
INTERFACE_TYPE = None
WIDTH = None
HEIGHT = None
COLOR_ORDER_BGR = False
GPIO_DATA_COMMAND = None
H_OFFSET = None
V_OFFSET = None

if PLATFORM == "pro":
    # ssd1351 128 x 128
    DISPLAY_TYPE = "ssd1351"
    INTERFACE_TYPE = "spi"
    WIDTH = "128"
    HEIGHT = "128"
    COLOR_ORDER_BGR = True
elif PLATFORM == "waveshare":
    # 1.44 in LCD Display HAT settings
    DISPLAY_TYPE = "st7735"
    INTERFACE_TYPE = "spi"
    WIDTH = "128"
    HEIGHT = "128"
    COLOR_ORDER_BGR = True
    GPIO_DATA_COMMAND = "25"
    H_OFFSET = "1"
    V_OFFSET = "2"
else:
    # Sapphire HAT OLED settings
    DISPLAY_TYPE = "sh1106"
    I2C_PORT = "0"
    WIDTH = "128"
    HEIGHT = "64"

### Legacy settings here for other displays ###
# Neo 2 OLED settings
#DISPLAY_TYPE = "ssd1306"
#I2C_PORT = 0

# ssd1327 128 x 128
#DISPLAY_TYPE = "ssd1327"
#I2C_ADDRESS = "0x3d"
#WIDTH = "128"
#HEIGHT = "128"


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

if COLOR_ORDER_BGR:
    actual_args.append("--bgr")

if GPIO_DATA_COMMAND:
    actual_args.append("--gpio-data-command")
    actual_args.append(GPIO_DATA_COMMAND)

if H_OFFSET:
    actual_args.append("--h-offset")
    actual_args.append(H_OFFSET)

if V_OFFSET:
    actual_args.append("--v-offset")
    actual_args.append(V_OFFSET)

device = get_device(actual_args=actual_args)

# Init function of the OLED
def init():
    if PLATFORM == "pro":
        # Reduce the contrast to also help reduce the noise
        # that's being produced by the display for some reason
        device.contrast(128)
    return True

def setNormalDisplay():
    return True

def setHorizontalMode():
    return True

def clearDisplay():
    #blank = Image.new("RGBA", device.size, "black")
    #device.display(blank.convert(device.mode))
    device.clear()

def drawImage(image):
    device.display(image.convert(device.mode))
    #device.display(image)
