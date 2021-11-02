# -*- coding: utf-8 -*-
#
"""
constants.py - shared constant vars
"""

from PIL import ImageFont
import os
import pathlib
from modules.env_utils import EnvUtils

__version__ = "2.0.2"
__author__ = "wifinigel@gmail.com"


env_util = EnvUtils()
PLATFORM = env_util.get_platform()

# set misc vars depending on platform type
HEIGHT_OFFSET = 0
IMAGE_DIR = "images/128x64"
MAX_TABLE_LINES = 4
MAX_PAGE_LINES = 3
DISPLAY_MODE = '1'

if PLATFORM == "pro":
    HEIGHT_OFFSET = 64
    IMAGE_DIR = "images/128x128"
    MAX_TABLE_LINES = 7
    MAX_PAGE_LINES = 6
    DISPLAY_MODE = 'RGB'


PAGE_SLEEP = 300             # Time in secs before sleep
PAGE_WIDTH = 128             # Pixel size of screen width
PAGE_HEIGHT = 64 + HEIGHT_OFFSET  # Pixel size of screen height
NAV_BAR_TOP = 54 + HEIGHT_OFFSET  # Top pixel number of nav bar
MENU_VERSION =  __version__  # fpms version

# figure out the script path
SCRIPT_PATH = str(pathlib.Path(__file__).parent.parent.absolute())

# change in to script path dir
os.chdir(SCRIPT_PATH)

# Define display fonts
SMART_FONT = ImageFont.truetype('fonts/DejaVuSansMono-Bold.ttf', 10)
FONT11 = ImageFont.truetype('fonts/DejaVuSansMono.ttf', 11)
FONT12 = ImageFont.truetype('fonts/DejaVuSansMono.ttf', 12)
FONTB12 =  ImageFont.truetype('fonts/DejaVuSansMono-Bold.ttf', 12)
FONT14 = ImageFont.truetype('fonts/DejaVuSansMono.ttf', 14)
FONTB14 =  ImageFont.truetype('fonts/DejaVuSansMono-Bold.ttf', 14)

#######################################
# File name constants
#######################################

# Linux programs
IFCONFIG_FILE = '/sbin/ifconfig'
IWCONFIG_FILE = '/sbin/iwconfig'
IW_FILE = '/sbin/iw'
UFW_FILE = '/usr/sbin/ufw'
ETHTOOL_FILE = '/sbin/ethtool'

# Mode changer scripts
MODE_FILE = '/etc/wlanpi-state'

# Version file for WLAN Pi image
WLANPI_IMAGE_FILE = '/etc/wlanpi-release'

WCONSOLE_SWITCHER_FILE ='/usr/bin/wconsole_switcher'
HOTSPOT_SWITCHER_FILE = '/usr/bin/hotspot_switcher'
WIPERF_SWITCHER_FILE = '/usr/bin/wiperf_switcher'
SERVER_SWITCHER_FILE = '/usr/bin/server_switcher'

#### Paths below here are relative to script dir or /tmp fixed paths ###

# Networkinfo data file names
LLDPNEIGH_FILE = '/tmp/lldpneigh.txt'
CDPNEIGH_FILE = '/tmp/cdpneigh.txt'
IPCONFIG_FILE = '/opt/wlanpi-common/networkinfo/ipconfig.sh 2>/dev/null'
REACHABILITY_FILE = '/opt/wlanpi-common/networkinfo/reachability.sh'
PUBLICIP_CMD = '/opt/wlanpi-common/networkinfo/publicip.sh'
BLINKER_FILE = '/opt/wlanpi-common/networkinfo/portblinker.sh'

# Button mapping (WLANPi Pro)
BUTTONS_WLANPI_PRO = {
    "up": 22,
    "down": 15,
    "left": 17,
    "right": 27,
    "center": 14,
}

# temp setup to test code using Sapphire HAT
# (center - middle front panel button, up/down = side wheel up/down)
BUTTONS_SAPPHIRE = {
    "up": 26,
    "down": 22,
    "left": 4,
    "right": 27,
    "center": 17,
}

BUTTONS_PINS = {}

if PLATFORM == "pro":
    BUTTONS_PINS = BUTTONS_WLANPI_PRO
else:
    BUTTONS_PINS = BUTTONS_SAPPHIRE
