#!/usr/bin/env python
# -*- coding: utf-8 -*-

from luma.core import cmdline, error
from PIL import Image
import sys
import logging

DISPLAY_TYPE = None
#I2C_PORT = None
#I2C_ADDRESS = None
INTERFACE_TYPE = None
WIDTH = None
HEIGHT = None

# Sapphire HAT OLED settings
#DISPLAY_TYPE = "sh1106"
#I2C_PORT = 1

# Neo 2 OLED settings
#DISPLAY_TYPE = "ssd1306"
#I2C_PORT = 0

# ssd1327 128 x 128
#DISPLAY_TYPE = "ssd1327"
#I2C_ADDRESS = "0x3d"
#WIDTH = "128"
#HEIGHT = "128"

# ssd1351 128 x 128
DISPLAY_TYPE = "ssd1351"
INTERFACE_TYPE = "spi"
WIDTH = "128"
HEIGHT = "128"

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

    return 'Version: {}\nDisplay: {}\n{}Dimensions: {} x {}\n{}'.format(
        version, args.display, iface, device.width, device.height, '-' * 60)


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

device = get_device(actual_args=actual_args)

# Init function of the OLED
def init():
    return True

def setNormalDisplay():
    return True

def setHorizontalMode():
    return True

def clearDisplay():
    blank = Image.new("RGBA", device.size, "black")
    device.display(blank.convert(device.mode))

def drawImage(image):
    device.display(image.convert(device.mode))
