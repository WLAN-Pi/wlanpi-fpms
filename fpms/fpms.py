# -*- coding: utf-8 -*-
#!/usr/bin/env python3

"""
FPMS
~~~~

Front Panel Menu System
"""

import getopt
import gpiod
import os
import os.path
import random
import signal
import socket
import subprocess
import sys
import termios
import threading
import time
import tty
import types

from PIL import Image, ImageDraw, ImageFont
from gpiod.line import Bias, Edge
from datetime import timedelta

# Check we're running as root
if not os.geteuid()==0:
    print("fpms must be run as root ... exiting ...")
    sys.exit(-1)

from .__version__ import __title__, __version__
from .modules import wlanpi_oled as oled
from .modules.apps.kismet import *
from .modules.apps.profiler import *
from .modules.apps.scanner import *
from .modules.bluetooth import *
from .modules.cloud_tests import CloudUtils
from .modules.constants import (
    BUTTONS_PINS,
    DISPLAY_MODE,
    IMAGE_DIR,
    MODE_FILE,
    NAV_BAR_TOP,
    PAGE_HEIGHT,
    PAGE_SLEEP,
    PAGE_WIDTH,
    SCRIPT_PATH,
    WLANPI_IMAGE_FILE,
)
from .modules.env_utils import EnvUtils
from .modules.modes import *
from .modules.nav.buttons import Button
from .modules.network import *
from .modules.pages.display import Display
from .modules.pages.homepage import HomePage
from .modules.pages.page import Page
from .modules.pages.pagedtable import PagedTable
from .modules.pages.simpletable import SimpleTable
from .modules.system import *
from .modules.battery import *
from .modules.utils import *
from .modules.reg_domain import *
from .modules.time_zone import *

def main():

    global running

    ####################################
    # Parse arguments
    ####################################

    def authors():
        authors = os.path.realpath(os.path.join(os.getcwd(), "AUTHORS.md"))
        if not os.path.isfile(authors):
            # Couldn't find authors
            print(authors)
            return ""
        else:
            with open(authors) as f:
                return "\n".join(filter(None, [line if line.startswith('*') else "" for line in f.read().splitlines()]))


    def usage():
        return """
usage: fpms [-a] [-h] [-e] [-v]

wlanpi-fpms drives the Front Panel Menu System on the WLAN Pi

optional options:
  -a                print authors
  -e                emulate buttons from keyboard
  -h                show this message and exit
  -v                show module version and exit
        """

    try:
        opts, _args = getopt.getopt(sys.argv[1:], ":ahev", ["authors", "help", "emulate-buttons", "version"])
    except getopt.GetoptError as error:
        print("{0} ... ".format(error))
        print(usage())
        sys.exit(2)

    emulate = False

    for opt, arg in opts:
        if opt in ['-e', "--emulate-buttons"]:
            emulate = True
        elif opt in ("-a", "--authors"):
            print(authors())
            sys.exit()
        elif opt in ("-h", "--help"):
            print(usage())
            sys.exit()
        elif opt in ("-v", "--version"):
            print("{0} {1}".format(__title__, __version__))
            sys.exit()
        else:
            assert False, "unhandled option"

    ####################################
    # Initialize the SEED OLED display
    ####################################
    oled.init()
    # Set display to normal mode (i.e non-inverse mode)
    oled.setNormalDisplay()
    oled.setHorizontalMode()

    #######################################
    # Initialize various global variables
    #######################################
    g_vars = {

        ##################################################
        # Shared status signals (may be changed anywhere)
        ##################################################

        # This variable is shared between activities and is set to True if a
        # drawing action in already if progress (e.g. by another activity). An activity
        # happens during each cycle of the main while loop or when a button is pressed
        # (This does not appear to be threading or process spawning)
        'drawing_in_progress': False,      # True when page being painted on screen

        'shutdown_in_progress': False,     # True when shutdown or reboot started
        'screen_cleared': False,           # True when display cleared (e.g. screen save)
        'display_state': 'page',           # current display state: 'page' or 'menu'
        'sig_fired': False,                # Set to True when button handler fired
        'option_selected': 0,              # Content of currently selected menu level
        'current_menu_location': [0],      # Pointer to current location in menu structure
        'current_scroll_selection': 0,     # where we currently are in scrolling table
        'current_mode': 'classic',         # Currently selected mode (e.g. wconsole/classic)
        'start_up': True,                  # True if in initial (home page) start-up state
        'disable_keys': False,             # Set to true when need to ignore key presses
        'table_list_length': 0,            # Total length of currently displayed table
        'table_pages': 1,                  # pages in current table
        'result_cache': False,             # used to cache results when paging info
        'speedtest_result_text': '',       # tablulated speedtest result data
        'button_press_count': 0,           # global count of button pressses
        'last_button_press_count': -1,     # copy of count of button pressses used in main loop
        'pageSleepCountdown': PAGE_SLEEP,  # Set page sleep control
        'home_page_name': "Home",          # Display name for top level menu
        'home_page_alternate': False,      # True if in alternate home page state
        'blinker_status': False,           # Blinker status
        'eth_carrier_status': 0,           # Eth0 physical link status
        'eth_last_known_address_set': None,# Last known ethernet addresses
        'eth_last_reachability_test': 0,       # Number of seconds elapsed since last reachability test
        'eth_last_reachability_result' : False,# Last reachability state
        'scan_file' : '',                  # Location to save scans
        'profiler_beaconing' : False,          # Indicates if the profiler is running
        'profiler_last_profile_date': None, # The date of the last profile
        'timezones_available' : [],         # The list of Timezones the system can support
        'timezone_selected' : None          # The timezone selected from the menu for use in other functions
    }

    ############################
    # shared objects
    ############################
    g_vars['image'] = Image.new(DISPLAY_MODE, (PAGE_WIDTH, PAGE_HEIGHT))
    g_vars['draw'] = ImageDraw.Draw(g_vars['image'])
    g_vars['reboot_image'] = Image.open(IMAGE_DIR + '/reboot.png').convert(DISPLAY_MODE)
    g_vars['shutdown_image'] = Image.open(IMAGE_DIR + '/shutdown.png').convert(DISPLAY_MODE)

    #####################################
    # check our current operating mode
    #####################################

    env_utils = EnvUtils()
    g_vars['current_mode'] = env_utils.get_mode(MODE_FILE)

    #######################################################################
    # Server mode non-persistence
    # If the Pi is in Server schedule mode switch to Classic for next boot
    #######################################################################

    if g_vars['current_mode'] == "server":
        schedule_server_to_classic = "/etc/wlanpi-server/scripts/schedule-switch-to-classic"
        subprocess.Popen([schedule_server_to_classic])

    ##################################
    # Static info we want to get once
    ##################################

    # get & the current version of WLANPi image
    g_vars['wlanpi_ver'] = env_utils.get_image_ver(WLANPI_IMAGE_FILE)

    # ################################
    # Other state initialization
    # ################################
    profiler = Profiler(g_vars)
    g_vars['profiler_last_profile_date'] = profiler.profiler_last_profile_date()
    g_vars['profiler_beaconing'] = profiler.profiler_beaconing()

    timezone = TimeZone(g_vars)
    timezones_available = timezone.get_timezones_menu_format()

    ###########################
    # Network menu area utils
    ###########################
    def show_interfaces():
        network_obj = Network(g_vars)
        network_obj.show_interfaces(g_vars)

    def show_wlan_interfaces():
        network_obj = Network(g_vars)
        network_obj.show_wlan_interfaces(g_vars)

    def show_eth0_ipconfig():
        network_obj = Network(g_vars)
        network_obj.show_eth0_ipconfig(g_vars)

    def show_vlan():
        network_obj = Network(g_vars)
        network_obj.show_vlan(g_vars)

    def show_lldp_neighbour():
        network_obj = Network(g_vars)
        network_obj.show_lldp_neighbour(g_vars)

    def show_cdp_neighbour():
        network_obj = Network(g_vars)
        network_obj.show_cdp_neighbour(g_vars)

    def show_publicip():
        network_obj = Network(g_vars)
        network_obj.show_publicip(g_vars)

    def show_publicip6():
        network_obj = Network(g_vars)
        network_obj.show_publicip(g_vars, ip_version=6)

    ###########################
    # Bluetooth menu area
    ###########################
    def bluetooth_status():
        bluetooth_obj = Bluetooth(g_vars)
        bluetooth_obj.bluetooth_status(g_vars)

    def bluetooth_pair():
        bluetooth_obj = Bluetooth(g_vars)
        bluetooth_obj.bluetooth_pair(g_vars)

    def bluetooth_on():
        bluetooth_obj = Bluetooth(g_vars)
        bluetooth_obj.bluetooth_on(g_vars)

    def bluetooth_off():
        bluetooth_obj = Bluetooth(g_vars)
        bluetooth_obj.bluetooth_off(g_vars)

    ###########################
    # Utils menu area
    ###########################
    def show_reachability():
        utils_obj = Utils(g_vars)
        utils_obj.show_reachability(g_vars)

    def show_speedtest():
        utils_obj = Utils(g_vars)
        utils_obj.show_speedtest(g_vars)

    def show_ruckus_test():
        utils_obj = CloudUtils(g_vars)
        utils_obj.test_ruckus_cloud(g_vars)

    def show_mist_test():
        utils_obj = CloudUtils(g_vars)
        utils_obj.test_mist_cloud(g_vars)

    def show_aruba_test():
        utils_obj = CloudUtils(g_vars)
        utils_obj.test_aruba_cloud(g_vars)

    def show_extreme_test():
        utils_obj = CloudUtils(g_vars)
        utils_obj.test_extreme_cloud(g_vars)

    def show_blinker():
        utils_obj = Utils(g_vars)
        utils_obj.show_blinker(g_vars)

    def stop_blinker():
        utils_obj = Utils(g_vars)
        utils_obj.stop_blinker(g_vars)

    def show_ssid_passphrase():
        utils_obj = Utils(g_vars)
        utils_obj.show_ssid_passphrase(g_vars)

    def show_usb():
        utils_obj = Utils(g_vars)
        utils_obj.show_usb(g_vars)

    def show_ufw():
        utils_obj = Utils(g_vars)
        utils_obj.show_ufw(g_vars)

    ############################
    # Modes area
    ############################
    def wconsole_switcher():
        mode_obj = Mode(g_vars)
        mode_obj.wconsole_switcher(g_vars)

    def hotspot_switcher():
        mode_obj = Mode(g_vars)
        mode_obj.hotspot_switcher(g_vars)

    def wiperf_switcher():
        mode_obj = Mode(g_vars)
        mode_obj.wiperf_switcher(g_vars)

    def server_switcher():
        mode_obj = Mode(g_vars)
        mode_obj.server_switcher(g_vars)

    def bridge_switcher():
        mode_obj = Mode(g_vars)
        mode_obj.bridge_switcher(g_vars)

    ###########################
    # Apps area
    ###########################
    def kismet_start():
        app_obj = Kismet(g_vars)
        app_obj.kismet_start(g_vars)

    def kismet_stop():
        app_obj = Kismet(g_vars)
        app_obj.kismet_stop(g_vars)

    def profiler_status():
        app_obj = Profiler(g_vars)
        app_obj.profiler_status(g_vars)

    def profiler_stop():
        app_obj = Profiler(g_vars)
        app_obj.profiler_stop(g_vars)

    def profiler_start():
        app_obj = Profiler(g_vars)
        app_obj.profiler_start(g_vars)

    def profiler_start_2dot4ghz():
        app_obj = Profiler(g_vars)
        app_obj.profiler_start_2dot4ghz(g_vars)

    def profiler_start_no11r():
        app_obj = Profiler(g_vars)
        app_obj.profiler_start_no11r(g_vars)

    def profiler_start_no11ax():
        app_obj = Profiler(g_vars)
        app_obj.profiler_start_no11ax(g_vars)

    def profiler_purge_reports():
        app_obj = Profiler(g_vars)
        app_obj.profiler_purge_reports(g_vars)

    def profiler_purge_files():
        app_obj = Profiler(g_vars)
        app_obj.profiler_purge_files(g_vars)

    def scanner_scan():
        app_obj = Scanner(g_vars)
        app_obj.scanner_scan(g_vars)

    def scanner_scan_nohidden():
        app_obj = Scanner(g_vars)
        app_obj.scanner_scan_nohidden(g_vars)

    def scanner_scan_tofile_csv():
        app_obj = Scanner(g_vars)
        app_obj.scanner_scan_tofile_csv(g_vars)

    def scanner_scan_tofile_pcap_start():
        app_obj = Scanner(g_vars)
        app_obj.scanner_scan_tofile_pcap_start(g_vars)

    def scanner_scan_tofile_pcap_stop():
        app_obj = Scanner(g_vars)
        app_obj.scanner_scan_tofile_pcap_stop(g_vars)

    ###########################
    # System menu area utils
    ###########################

    def shutdown():
        system_obj = System(g_vars)
        system_obj.shutdown(g_vars)

    def reboot():
        system_obj = System(g_vars)
        system_obj.reboot(g_vars)

    def show_summary():
        system_obj = System(g_vars)
        system_obj.show_summary(g_vars)

    def show_battery():
        system_obj = Battery(g_vars)
        system_obj.show_battery(g_vars)

    def show_reg_domain():
        system_obj = RegDomain(g_vars)
        system_obj.show_reg_domain(g_vars)

    def set_reg_domain_us():
        system_obj = RegDomain(g_vars)
        system_obj.set_reg_domain_us(g_vars)

    def set_reg_domain_gb():
        system_obj = RegDomain(g_vars)
        system_obj.set_reg_domain_gb(g_vars)

    def set_reg_domain_br():
        system_obj = RegDomain(g_vars)
        system_obj.set_reg_domain_br(g_vars)

    def set_reg_domain_fr():
        system_obj = RegDomain(g_vars)
        system_obj.set_reg_domain_fr(g_vars)

    def set_reg_domain_cz():
        system_obj = RegDomain(g_vars)
        system_obj.set_reg_domain_cz(g_vars)

    def set_reg_domain_de():
        system_obj = RegDomain(g_vars)
        system_obj.set_reg_domain_de(g_vars)

    def show_date():
        system_obj = System(g_vars)
        system_obj.show_date(g_vars)

    def set_time_zone_auto():
        system_obj = TimeZone(g_vars)
        system_obj.set_time_zone_auto(g_vars)

    def set_time_zone():
        g_vars['timezone_selected'] = (timezones_available[g_vars['current_menu_location'][5]]['country'] +
        "/" +
        timezones_available[g_vars['current_menu_location'][5]]['timezones'][g_vars['current_menu_location'][6]])

        system_obj = TimeZone(g_vars)
        system_obj.set_time_zone_from_gvars(g_vars)

    def show_about():
        system_obj = System(g_vars)
        system_obj.show_about(g_vars)

    def show_help():
        system_obj = System(g_vars)
        system_obj.show_help(g_vars)

    def check_for_updates():
        system_obj = System(g_vars)
        system_obj.check_for_updates(g_vars)

    def install_updates():
        system_obj = System(g_vars)
        system_obj.install_updates(g_vars)

    #############################
    # Button presses & home page
    #############################
    def home_page():
        homepage_obj = HomePage(g_vars)
        homepage_obj.home_page(g_vars, menu)

    def menu_down():
        button_obj = Button(g_vars, menu)
        button_obj.menu_down(g_vars, menu)

    def menu_up():
        button_obj = Button(g_vars, menu)
        button_obj.menu_up(g_vars, menu)

    def menu_left():
        button_obj = Button(g_vars, menu)
        button_obj.menu_left(g_vars, menu)

    def menu_right():
        button_obj = Button(g_vars, menu)
        button_obj.menu_right(g_vars, menu)

    def menu_center():
        button_obj = Button(g_vars, menu)
        button_obj.menu_center(g_vars, menu)

    def menu_key1():
        shortcuts = [
            create_shortcut(menu, ["Utils",   "Reachability"]),
            create_shortcut(menu, ["Network", "LLDP Neighbour"]),
            create_shortcut(menu, ["Network", "Eth0 IP Config"])
        ]

        option_selected = g_vars['option_selected']

        option_index = 0
        option_found = False

        if g_vars['display_state'] == 'page':
            for shortcut in shortcuts:
                if option_selected == shortcut[-1]:
                    option_found = True
                    break
                option_index += 1

        next_index = 0
        if option_found:
            next_index = (option_index + 1) % len(shortcuts)

        next_shortcut = shortcuts[next_index]
        button_obj = Button(g_vars, menu)
        button_obj.shortcut(g_vars, menu, next_shortcut)

    def menu_key2():
        shortcut = create_shortcut(menu, ["Mode", "Classic Mode"])
        if g_vars['current_mode'] == "classic":
            shortcut = create_shortcut(menu, ["Modes", "Hotspot"])

        # Switch to menu item
        button_obj = Button(g_vars, menu)
        button_obj.shortcut(g_vars, menu, shortcut)

    def menu_key3():
        index = 0
        reboot_shortcut = create_shortcut(menu, ["System", "Reboot"])
        shutdown_shortcut = create_shortcut(menu, ["System", "Shutdown"])

        # Select the next path
        next_shortcut = reboot_shortcut
        if g_vars['current_menu_location'][:-1] == reboot_shortcut:
            next_shortcut = shutdown_shortcut

        # Switch to menu
        button_obj = Button(g_vars, menu)
        button_obj.shortcut(g_vars, menu, next_shortcut)

    def create_shortcut(menu, path, location=[]):

        if isinstance(menu, types.FunctionType):
            if len(path) > 0:
                raise Exception("invalid path")
            return [menu]

        if len(path) > 0:
            index = 0
            for item in menu:
                if item["name"] == path[0]:
                    return [index] + create_shortcut(item["action"], path[1:], location)
                index += 1

        return []

    #######################
    # menu structure here
    #######################


    # translate the timezone list into menu items (needs to be after definition of set_time_zone)
    for timezones_country in timezones_available:
        g_vars['timezones_available'].append({"name": timezones_country['country'], "action": []})
        for timezone in timezones_country['timezones']:
            g_vars['timezones_available'][-1]['action'].append({"name": timezone, "action": set_time_zone})

    # assume classic mode menu initially...
    menu = [
        {"name": "Network", "action": [
            {"name": "Interfaces", "action": show_interfaces},
            {"name": "WLAN Interfaces", "action": show_wlan_interfaces},
            {"name": "Eth0 IP Config", "action": show_eth0_ipconfig},
            {"name": "Eth0 VLAN", "action": show_vlan},
            {"name": "LLDP Neighbour", "action": show_lldp_neighbour},
            {"name": "CDP Neighbour", "action": show_cdp_neighbour},
            {"name": "Public IPv4", "action": show_publicip},
            {"name": "Public IPv6", "action": show_publicip6},
        ]
        },
        {"name": "Bluetooth", "action": [
            {"name": "Status", "action": bluetooth_status},
            {"name": "Turn On", "action": bluetooth_on},
            {"name": "Turn Off", "action": bluetooth_off},
            {"name": "Pair Device", "action": bluetooth_pair},
        ]
        },
        {"name": "Utils", "action": [
            {"name": "Reachability", "action": show_reachability},
            {"name": "Speedtest", "action": [
                {"name": "Run Test", "action": show_speedtest},
            ]
            },
            {"name": "Cloud Tests", "action": [
                {"name": "Aruba Central", "action": show_aruba_test},
                {"name": "ExtremeCloud IQ", "action": show_extreme_test},
                {"name": "Mist Cloud", "action": show_mist_test},
                {"name": "RUCKUS Cloud", "action": show_ruckus_test},
            ]
            },
            {"name": "Port Blinker", "action": [
                {"name": "Start", "action": show_blinker},
                {"name": "Stop", "action": stop_blinker},
            ]
            },
            {"name": "SSID/Passphrase", "action": show_ssid_passphrase},
            {"name": "USB Devices", "action": show_usb},
            {"name": "UFW Ports", "action": show_ufw},
        ]
        },
        {"name": "Modes", "action": [
            {"name": "Wi-Fi Console",   "action": [
                {"name": "Confirm", "action": wconsole_switcher},
            ]
            },
            {"name": "Hotspot",   "action": [
                {"name": "Confirm", "action": hotspot_switcher},
            ]
            },
            #{"name": "Wiperf",   "action": [
            #    {"name": "Confirm", "action": wiperf_switcher},
            #]
            #},
            {"name": "Server",   "action": [
                {"name": "Confirm", "action": server_switcher},
            ]
            },
            {"name": "Bridge",   "action": [
                {"name": "Confirm", "action": bridge_switcher},
            ]
            },
        ]
        },
        {"name": "Apps", "action": [
            {"name": "Kismet", "action": [
                {"name": "Start", "action": kismet_start},
                {"name": "Stop", "action": kismet_stop},
            ]
            },
            {"name": "Profiler",   "action": [
                {"name": "Status", "action":          profiler_status},
                {"name": "Stop", "action":            profiler_stop},
                {"name": "Start", "action":           profiler_start},
                {"name": "Start 2.4 GHz", "action":   profiler_start_2dot4ghz},
                {"name": "Start (no 11r)", "action":  profiler_start_no11r},
                {"name": "Start (no 11ax)", "action": profiler_start_no11ax},
                {"name": "Purge Reports", "action": [
                    {"name": "Confirm", "action": profiler_purge_reports},
                ]
                },
                {"name": "Purge Files", "action": [
                    {"name": "Confirm", "action": profiler_purge_files},
                ]
                }
            ]
            },
            {"name": "Scanner", "action": [
                {"name": "Scan", "action": scanner_scan},
                {"name": "Scan (no hidden)", "action": scanner_scan_nohidden},
                {"name": "Scan to CSV", "action": scanner_scan_tofile_csv},
                {"name": "Scan to PCAP", "action": [
                    {"name": "Start", "action" : scanner_scan_tofile_pcap_start},
                    {"name": "Stop", "action" : scanner_scan_tofile_pcap_stop}
                ]}
            ]
            },
        ]
        },
        {"name": "System", "action": [
            {"name": "About", "action": show_about},
            {"name": "Help", "action": show_help},
            {"name": "Summary", "action": show_summary},
            {"name": "Battery", "action": show_battery},
            {"name": "Settings", "action": [
                {"name": "Date & Time", "action": [
                    {"name": "Show Time & Zone", "action": show_date},
                    {"name": "Set Timezone", "action": [
                        {"name": "Auto", "action" : set_time_zone_auto},
                        {"name": "Manual", "action": g_vars['timezones_available']}
                    ]},
                ]},
                {"name": "RF Domain", "action": [
                    {"name": "Show Domain", "action": show_reg_domain},
                    {"name": "Set Domain US", "action": [
                        {"name": "Confirm & Reboot", "action": set_reg_domain_us},]},
                    {"name": "Set Domain GB", "action": [
                        {"name": "Confirm & Reboot", "action": set_reg_domain_gb},]},
                    {"name": "Set Domain BR", "action": [
                        {"name": "Confirm & Reboot", "action": set_reg_domain_br},]},
                    {"name": "Set Domain FR", "action": [
                        {"name": "Confirm & Reboot", "action": set_reg_domain_fr},]},
                    {"name": "Set Domain CZ", "action": [
                        {"name": "Confirm & Reboot", "action": set_reg_domain_cz},]},
                    {"name": "Set Domain DE", "action": [
                        {"name": "Confirm & Reboot", "action": set_reg_domain_de},]},
                ]},
            ]},
            {"name": "Reboot",   "action": [
                {"name": "Confirm", "action": reboot},
            ]
            },
            {"name": "Shutdown", "action": [
                {"name": "Confirm", "action": shutdown},
            ]
            },
        ]
        },
    ]

    # update menu options data structure if we're in non-classic mode
    if g_vars['current_mode'] == "wconsole":
        switcher_dispatcher = wconsole_switcher
        g_vars['home_page_name'] = "Wi-Fi Console"

    if g_vars['current_mode'] == "hotspot":
        switcher_dispatcher = hotspot_switcher
        g_vars['home_page_name'] = "Hotspot"

    if g_vars['current_mode'] == "wiperf":
        switcher_dispatcher = wiperf_switcher
        g_vars['home_page_name'] = "Wiperf"

    if g_vars['current_mode'] == "server":
        switcher_dispatcher = server_switcher
        g_vars['home_page_name'] = "Server"

    if g_vars['current_mode'] == "bridge":
        switcher_dispatcher = bridge_switcher
        g_vars['home_page_name'] = "Bridge"

    if g_vars['current_mode'] == "classic":
        # Remove Utils > SSID/Passphrase
        for item in menu:
            if item["name"] == "Utils":
                for action in item["action"]:
                    if action["name"] == "SSID/Passphrase":
                        item["action"].remove(action)
                        break
    else:
        # Adjust Modes menu
        for item in menu:
            if item["name"] == "Modes":
                item["name"] = "Mode"
                item["action"] = [
                    {"name": "Classic Mode",   "action": [
                        {"name": "Confirm", "action": switcher_dispatcher},
                    ]
                    },
                ]
                break

        # Remove Apps menu
        for item in menu:
            if item["name"] == "Apps":
                menu.remove(item)

    # Set up handlers to process key presses
    def button_press(gpio_pin, g_vars=g_vars):

        DOWN_KEY = BUTTONS_PINS['down']
        UP_KEY = BUTTONS_PINS['up']
        RIGHT_KEY = BUTTONS_PINS['right']
        LEFT_KEY = BUTTONS_PINS['left']
        CENTER_KEY = BUTTONS_PINS['center']
        KEY1 = None
        KEY2 = None
        KEY3 = None

        if 'key1' in BUTTONS_PINS:
            KEY1 = BUTTONS_PINS['key1']

        if 'key2' in BUTTONS_PINS:
            KEY2 = BUTTONS_PINS['key2']

        if 'key3' in BUTTONS_PINS:
            KEY3 = BUTTONS_PINS['key3']

        if g_vars['disable_keys'] == True:
            # someone disabled the front panel keys as they don't want to be interrupted
            return

        if (g_vars['sig_fired']):
            # signal handler already in progress, ignore this one
            return

        # user pressed a button, reset the sleep counter
        g_vars['pageSleepCountdown'] = PAGE_SLEEP

        g_vars['start_up'] = False

        if g_vars['drawing_in_progress'] or g_vars['shutdown_in_progress']:
            return

        # increment the button press counter to indicate the something has been done
        # and a page refresh is required
        g_vars['button_press_count'] += 1

        # if display has been switched off to save screen, power back on and show home menu
        if g_vars['screen_cleared']:
            wakeup_screen()
            return

        # Down key pressed
        if gpio_pin == DOWN_KEY:
            g_vars['sig_fired'] = True
            menu_down()
            g_vars['sig_fired'] = False
            return

        # Down key pressed
        if gpio_pin == UP_KEY:
            g_vars['sig_fired'] = True
            menu_up()
            g_vars['sig_fired'] = False
            return

        # Right/Selection key pressed
        if gpio_pin == RIGHT_KEY:
            g_vars['sig_fired'] = True
            menu_right()
            g_vars['sig_fired'] = False
            return

        # Left/Back key
        if gpio_pin == LEFT_KEY:
            g_vars['sig_fired'] = True
            menu_left()
            g_vars['sig_fired'] = False
            return

        # Center key
        if gpio_pin == CENTER_KEY:
            g_vars['sig_fired'] = True
            menu_center()
            g_vars['sig_fired'] = False
            return

        # Key 1
        if gpio_pin == KEY1:
            g_vars['sig_fired'] = True
            menu_key1()
            g_vars['sig_fired'] = False
            return

        # Key 2
        if gpio_pin == KEY2:
            g_vars['sig_fired'] = True
            menu_key2()
            g_vars['sig_fired'] = False
            return

        # Key 3
        if gpio_pin == KEY3:
            g_vars['sig_fired'] = True
            menu_key3()
            g_vars['sig_fired'] = False
            return

    ###############################################################################
    #
    # ****** MAIN *******
    #
    ###############################################################################

    # First time around (power-up), draw logo on display
    '''
    rogues_gallery = [
        IMAGE_DIR + '/wlanprologo',
        IMAGE_DIR + '/wlanprologo.png',
        IMAGE_DIR + '/joshschmelzle.png',
        IMAGE_DIR + '/crv.png',
        IMAGE_DIR + '/jolla.png',
        IMAGE_DIR + '/wifinigel.png',
        IMAGE_DIR + '/dansfini.png',
        IMAGE_DIR + '/jiribrejcha.png'
    ]

    random_image = random.choice(rogues_gallery)
    image0 = Image.open(random_image).convert(DISPLAY_MODE)
    oled.drawImage(image0)
    time.sleep(2.0)
    '''

    ###############################################################################
    # Splash screen
    ###############################################################################

    # First time around (power-up), animate logo on display
    splash_screen_images = [
        IMAGE_DIR + '/wlanpi0.png',
        IMAGE_DIR + '/wlanpi1.png',
        IMAGE_DIR + '/wlanpi2.png',
        IMAGE_DIR + '/wlanpi3.png',
        IMAGE_DIR + '/wlanpi4.png'
    ]

    for image in splash_screen_images:
        img = Image.open(image).convert(DISPLAY_MODE)
        oled.drawImage(img)
        time.sleep(0.100)

    # Leave logo on screen some more time
    time.sleep(2)

    ###############################################################################
    # Buttons setup
    ###############################################################################

    # Set signal handlers for button presses - these fire every time a button
    # is pressed
    def up_key():
        button_press(BUTTONS_PINS['up'], g_vars)

    def down_key():
        button_press(BUTTONS_PINS['down'], g_vars)

    def left_key():
        button_press(BUTTONS_PINS['left'], g_vars)

    def right_key():
        button_press(BUTTONS_PINS['right'], g_vars)

    def center_key():
        button_press(BUTTONS_PINS['center'], g_vars)

    def key_1():
        button_press(BUTTONS_PINS['key1'], g_vars)

    def key_2():
        button_press(BUTTONS_PINS['key2'], g_vars)

    def key_3():
        button_press(BUTTONS_PINS['key3'], g_vars)

    def monitor_buttons():

        line_setting = gpiod.LineSettings(
            bias=Bias.PULL_UP,
            edge_detection=Edge.FALLING,
            debounce_period=timedelta(microseconds=10)
        )

        lines = {k:line_setting for k in BUTTONS_PINS.values()}

        with gpiod.request_lines(
            "/dev/gpiochip0",
            lines,
        ) as request:
            while True:
                request.wait_edge_events(1)
                events = request.read_edge_events()

                for event in events:
                    if event.line_offset == BUTTONS_PINS['up']:
                        up_key()
                    elif event.line_offset == BUTTONS_PINS['down']:
                        down_key()
                    elif event.line_offset == BUTTONS_PINS['left']:
                        left_key()
                    elif event.line_offset == BUTTONS_PINS['right']:
                        right_key()
                    elif event.line_offset == BUTTONS_PINS['center']:
                        center_key()
                    elif event.line_offset == BUTTONS_PINS['key1']:
                        key_1()
                    elif event.line_offset == BUTTONS_PINS['key2']:
                        key_2()
                    elif event.line_offset == BUTTONS_PINS['key3']:
                        key_3()


    m = threading.Thread(name="button-monitor", target=monitor_buttons)
    m.daemon = True
    m.start()

    button_key1_present = 'key1' in BUTTONS_PINS
    button_key2_present = 'key2' in BUTTONS_PINS
    button_key3_present = 'key3' in BUTTONS_PINS

    running = True

    ##############################################################################
    # Emulate button presses using a keyboard
    ##############################################################################

    def getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def emulate_buttons():

        global running

        while True:
            char = getch()

            if (char == "k" or char == "K"):
                running = False
                break

            if (char == "g" or char == "G"):
                capture_screen()

            if (char == "8" or char == "w"):
                up_key()

            if (char == "2" or char == "x"):
                down_key()

            if (char == "4" or char == "a"):
                left_key()

            if (char == "6" or char == "d"):
                right_key()

            if (char == "5" or char == "s"):
                center_key()

            if button_key1_present:
                if (char == "*" or char == "i"):
                    key_1()

            if button_key2_present:
                if (char == "-" or char == "o"):
                    key_2()

            if button_key3_present:
                if (char == "+" or char == "p"):
                    key_3()

    if emulate:
        print("UP = 'w', DOWN = 'x', LEFT = 'a', RIGHT = 'd', CENTER = 's'")
        if button_key1_present and button_key2_present and button_key3_present:
            print("KEY1 = 'i', KEY2 = 'o', KEY3 = 'p'")
        print("Press 'g' to capture the screen.")
        print("Press 'k' to terminate.")
        e = threading.Thread(name="button-emulator", target=emulate_buttons)
        e.daemon = True
        e.start()

    ##############################################################################
    # Helper functions
    ##############################################################################
    def capture_screen():
        g_vars['sig_fired'] = True
        screenshots_dir = "/home/wlanpi/screenshots"
        if not os.path.exists(screenshots_dir):
            os.makedirs(screenshots_dir)
        timestr = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")
        save_file = screenshots_dir + "/screenshot_" + timestr + ".png"
        g_vars['image'].save(save_file)
        print(save_file)
        g_vars['sig_fired'] = False

    def sleep_screen():
        oled.sleep()
        g_vars['screen_cleared'] = True

    def wakeup_screen():
        oled.wakeup()
        g_vars['screen_cleared'] = False
        g_vars['pageSleepCountdown'] = PAGE_SLEEP

    def check_eth():
        '''
        Detects a change in the status of the Ethernet port and wakes up
        the screen if necessary
        '''
        try:
            cmd = "cat /sys/class/net/eth0/carrier"
            carrier = int(subprocess.check_output(cmd, shell=True).decode().strip())
            if g_vars['eth_carrier_status'] != carrier:
                wakeup_screen()
            g_vars['eth_carrier_status'] = carrier
        except subprocess.CalledProcessError as exc:
            pass

    ##############################################################################
    # Constant 'while' loop to paint images on display or execute actions in
    # response to selections made with buttons. When any of the 3 WLANPi buttons
    # are pressed, I believe the signal handler takes over the Python interpreter
    # and executes the code associated with the button. The original flow continues
    # once the button press action has been completed.
    #
    # The current sleep period of the while loop is ignored when a button is
    # pressed.
    #
    # All global variables defined outside of the while loop are preserved and may
    # read/set as required. The same variables are available for read/write even
    # when a button is pressed and an interrupt occurs: no additional thread or
    # interpreter with its own set of vars appears to be launched. For this reason,
    # vars may be used to signal between the main while loop and any button press
    # activity to indicate that processes such as screen paints are in progress.
    #
    # Despite the sample code suggesting threading is used I do not believe this
    # is the case, based on testing with variable scopes and checking for process
    # IDs when different parts of the script are executing.
    ##############################################################################
    while running:

        try:

            # check if eth0 link status has changed so we exit from screen save if needed
            check_eth()

            if g_vars['shutdown_in_progress'] or g_vars['screen_cleared'] or g_vars['drawing_in_progress'] or g_vars['sig_fired']:

                # we don't really want to do anything at the moment, lets
                # nap and loop around
                time.sleep(2)
                continue

            # Draw a menu or execute current action (dispatcher)
            if g_vars['display_state'] != 'menu':
                # no menu shown, so must be executing action.

                # if we've just booted up, show home page
                if g_vars['start_up'] == True:
                    g_vars['option_selected'] = home_page

                # Re-run current action to refresh screen
                #
                # Handle when g_vars['option_selected'] does not return
                #   a func but returns a list instead and fpms freezes.
                #
                # investigate by uncommenting these print statements
                # and `tail -f /tmp/nanoled-python.log`:
                # print(g_vars['option_selected'])
                # print(type(g_vars['option_selected']))

                if isinstance(g_vars['option_selected'], types.FunctionType):
                    g_vars['option_selected']()

            else:
                # lets try drawing our page (or refresh if already painted)

                # No point in repainting screen if we are on a
                # menu page and no buttons pressed since last loop cycle
                # In reality, this condition will rarely (if ever) be true
                # as the page painting is driven from the key press which
                # interrupts this flow anyhow. Left in as a safeguard
                if g_vars['button_press_count'] > g_vars['last_button_press_count']:
                    page_obj = Page(g_vars)
                    page_obj.draw_page(g_vars, menu)

            # if screen timeout is zero, clear it if not already done (blank the
            # display to reduce screenburn)
            if g_vars['pageSleepCountdown'] == 0 and g_vars['screen_cleared'] == False:
                sleep_screen()

            g_vars['pageSleepCountdown'] = g_vars['pageSleepCountdown'] - 1

            # have a nap before we start our next loop
            time.sleep(2)

        except KeyboardInterrupt:
            break
        except IOError as ex:
            print("Error " + str(ex))

        g_vars['last_button_press_count'] = g_vars['button_press_count']

    '''
    Discounted ideas

        1. Vary sleep timer for main while loop (e.g. longer for less frequently
           updating data) - doesn;t work as main while loop may be in middle of
           long sleep when button action taken, so screen refresh very long.

    '''
