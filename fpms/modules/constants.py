# -*- coding: utf-8 -*-
#
"""
constants.py - shared constant vars
"""

from PIL import ImageFont
import os
import pathlib
from fpms.modules.env_utils import EnvUtils
from fpms.modules.platform import *
from fpms.modules.display import *

__version__ = "2.0.3"
__author__ = "wifinigel@gmail.com"

# Model file for WLAN Pi
WLANPI_MODEL_FILE = '/etc/wlanpi-model'

# Version file for WLAN Pi image
WLANPI_IMAGE_FILE = '/etc/wlanpi-release'

env_util = EnvUtils()
PLATFORM = env_util.get_platform(WLANPI_MODEL_FILE)
DISPLAY_TYPE = env_util.get_display_type(PLATFORM)
# Uncomment the line below to force a display type
#DISPLAY_TYPE = DISPLAY_TYPE_ST7789

IMAGE_DIR = "images/128x128"
MAX_TABLE_LINES = 9
MAX_PAGE_LINES = 8
DISPLAY_MODE = 'RGB'

PAGE_SLEEP = 300 # Time in secs before sleep, Set to -1 to disable sleep, default 300
PAGE_WIDTH = 128 # Pixel size of screen width
PAGE_HEIGHT = 128 # Pixel size of screen height
NAV_BAR_TOP = PAGE_HEIGHT - 10 # Top pixel number of nav bar
STATUS_BAR_HEIGHT = 16
SYSTEM_BAR_HEIGHT = 15

MENU_VERSION =  __version__  # fpms version

# figure out the script path
SCRIPT_PATH = str(pathlib.Path(__file__).parent.parent.absolute())

# change in to script path dir
os.chdir(SCRIPT_PATH)

# Define display fonts
TINY_FONT = ImageFont.truetype('fonts/DejaVuSansMono.ttf', 7)
SMART_FONT = ImageFont.truetype('fonts/DejaVuSansMono-Bold.ttf', 10)
FONT10 = ImageFont.truetype('fonts/DejaVuSansMono.ttf', 10)
FONT11 = ImageFont.truetype('fonts/DejaVuSansMono.ttf', 11)
FONT12 = ImageFont.truetype('fonts/DejaVuSansMono.ttf', 12)
FONT13 = ImageFont.truetype('fonts/DejaVuSansMono.ttf', 13)
FONT14 = ImageFont.truetype('fonts/DejaVuSansMono.ttf', 14)
FONTB10 =  ImageFont.truetype('fonts/DejaVuSansMono-Bold.ttf', 10)
FONTB11 =  ImageFont.truetype('fonts/DejaVuSansMono-Bold.ttf', 11)
FONTB12 =  ImageFont.truetype('fonts/DejaVuSansMono-Bold.ttf', 12)
FONTB13 =  ImageFont.truetype('fonts/DejaVuSansMono-Bold.ttf', 13)
FONTB14 =  ImageFont.truetype('fonts/DejaVuSansMono-Bold.ttf', 14)
ICONS = ImageFont.truetype('fonts/ionicons.ttf', 13)

#######################################
# File name constants
#######################################

# Linux programs
IFCONFIG_FILE = '/sbin/ifconfig'
IW_FILE = '/sbin/iw'
IP_FILE = '/usr/sbin/ip'
UFW_FILE = '/usr/sbin/ufw'
ETHTOOL_FILE = '/sbin/ethtool'

# Mode changer scripts
MODE_FILE = '/etc/wlanpi-state'

WCONSOLE_SWITCHER_FILE ='/opt/wlanpi-wconsole/wconsole_switcher'
HOTSPOT_SWITCHER_FILE = '/opt/wlanpi-hotspot/hotspot_switcher'
WIPERF_SWITCHER_FILE = '/opt/wlanpi-wiperf/wiperf_switcher'
SERVER_SWITCHER_FILE = '/opt/wlanpi-server/server_switcher'
BRIDGE_SWITCHER_FILE = '/opt/wlanpi-bridge/bridge_switcher'

REG_DOMAIN_FILE = '/usr/bin/wlanpi-reg-domain'
TIME_ZONE_FILE= '/usr/bin/wlanpi-timezone'

#### Paths below here are relative to script dir or /tmp fixed paths ###

# Networkinfo data file names
LLDPNEIGH_FILE = '/tmp/lldpneigh.txt'
CDPNEIGH_FILE = '/tmp/cdpneigh.txt'
IPCONFIG_FILE = '/opt/wlanpi-common/networkinfo/ipconfig.sh 2>/dev/null'
REACHABILITY_FILE = '/opt/wlanpi-common/networkinfo/reachability.sh'
PUBLICIP_CMD = '/opt/wlanpi-common/networkinfo/publicip.sh'
PUBLICIP6_CMD = '/opt/wlanpi-common/networkinfo/publicip6.sh'
BLINKER_FILE = '/opt/wlanpi-common/networkinfo/portblinker.sh'

# Battery status file
BATTERY_STATUS_FILE = '/sys/class/power_supply/bq27546-0/uevent'
#BATTERY_STATUS_FILE = '/home/wlanpi/battery_status.txt'

# Button mapping (WLANPi Pro)
BUTTONS_WLANPI_PRO = {
    "up": 22,
    "down": 5,
    "left": 17,
    "right": 27,
    "center": 6,
}

# Button mapping for the Waveshare 1.44 inch LCD Display HAT
# https://www.waveshare.com/1.44inch-lcd-hat.htm
BUTTONS_WAVESHARE = {
    "up": 6,
    "down": 19,
    "left": 5,
    "right": 26,
    "center": 13,
    "key1": 21,
    "key2": 20,
    "key3": 16
}
# temp setup to test code using Sapphire HAT
# (center - middle front panel button, up/down = side wheel up/down)
BUTTONS_SAPPHIRE = {
    "up": 26,
    "down": 22,
    "left": 4,
    "right": 27,
    "center": 17
}

BUTTONS_PINS = {}

if PLATFORM == PLATFORM_PRO:
    BUTTONS_PINS = BUTTONS_WLANPI_PRO
else:
    BUTTONS_PINS = BUTTONS_WAVESHARE
