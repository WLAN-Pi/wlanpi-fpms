#!/usr/bin/env python3

"""
FPMS
~~~~

Front Panel Menu System
"""

import configparser
import getopt
import os
import os.path
import sys
import syslog
import termios
import threading
import time
import tty
import types
from datetime import datetime, timedelta
from typing import Any

import dbus
import dbus.mainloop.glib
import gpiod
from gi.repository import GLib
from gpiod.line import Bias, Edge
from PIL import Image, ImageDraw

if not os.geteuid() == 0:
    print("fpms must be run as root ... exiting ...")
    sys.exit(-1)

from .__version__ import __title__, __version__
from .modules import wlanpi_oled as oled
from .modules.apps.kismet import *
from .modules.apps.profiler import *
from .modules.apps.scanner import *
from .modules.battery import *
from .modules.bluetooth import *
from .modules.cloud_tests import CloudUtils
from .modules.constants import *
from .modules.env_utils import EnvUtils
from .modules.nav.buttons import Button
from .modules.network import *
from .modules.pages.homepage import HomePage
from .modules.pages.page import Page
from .modules.reg_domain import *
from .modules.system import *
from .modules.time_zone import *
from .modules.utils import *

FPMS_CONF_FILE = "/etc/wlanpi-fpms.conf"

g_vars: dict[str, Any] = {
    "display_orientation": DISPLAY_ORIENTATION_NORMAL,
    "drawing_in_progress": False,
    "shutdown_in_progress": False,
    "screen_cleared": False,
    "display_state": "page",
    "sig_fired": False,
    "option_selected": 0,
    "current_menu_location": [0],
    "current_scroll_selection": 0,
    "current_mode": "classic",
    "start_up": True,
    "disable_keys": False,
    "table_list_length": 0,
    "table_pages": 1,
    "result_cache": False,
    "speedtest_result_text": "",
    "button_press_count": 0,
    "last_button_press_count": -1,
    "pageSleepCountdown": PAGE_SLEEP,
    "home_page_name": "Home",
    "home_page_alternate": False,
    "blinker_status": False,
    "eth_carrier_status": 0,
    "eth_last_known_address_set": None,
    "eth_last_reachability_test": 0,
    "eth_last_reachability_result": False,
    "scan_file": "",
    "profiler_beaconing": False,
    "profiler_last_profile_date": None,
    "timezones_available": [],
    "timezone_selected": None,
}


def log_to_syslog(message, level=syslog.LOG_INFO):
    syslog.openlog(ident="fpms", logoption=syslog.LOG_PID, facility=syslog.LOG_USER)
    syslog.syslog(level, message)
    syslog.closelog()


def _release_shutdown_inhibitor():
    """Release the delay lock once, even if both shutdown signals arrive."""
    inhibitor_fd = g_vars.pop("shutdown_inhibitor_fd", None)
    if inhibitor_fd is not None:
        os.close(inhibitor_fd)


def handle_reboot_or_shutdown(shutdown=False):
    global g_vars
    log_to_syslog(f"shutdown_in_progress: {g_vars['shutdown_in_progress']}")
    try:
        if not g_vars["shutdown_in_progress"]:
            g_vars["shutdown_in_progress"] = True
            log_to_syslog("Drawing shutdown/reboot image")
            if shutdown:
                oled.final_frame(g_vars["shutdown_image"])
            else:
                oled.final_frame(g_vars["reboot_image"])
            log_to_syslog("Shutdown/reboot image drawn")
    finally:
        _release_shutdown_inhibitor()


def handle_prepare_for_shutdown(arg):
    log_to_syslog("PrepareForShutdown signal received")
    handle_reboot_or_shutdown()


def handle_jobnew(*args):
    log_to_syslog("JobNew signal received")
    for arg in args:
        if isinstance(arg, str):
            if "reboot.target" in arg:
                handle_reboot_or_shutdown()
            elif ("halt.target" in arg) or ("poweroff.target" in arg):
                handle_reboot_or_shutdown(True)


dbus_handlers_ready = threading.Event()


def run_dbus_loop():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()

    login1_proxy = bus.get_object("org.freedesktop.login1", "/org/freedesktop/login1")
    login1 = dbus.Interface(login1_proxy, "org.freedesktop.login1.Manager")

    g_vars["shutdown_inhibitor_fd"] = login1.Inhibit(
        "shutdown", "fpms", "Delaying shutdown", "delay"
    ).take()

    bus.add_signal_receiver(
        handle_prepare_for_shutdown,
        signal_name="PrepareForShutdown",
        dbus_interface="org.freedesktop.login1.Manager",
        bus_name="org.freedesktop.login1",
        path="/org/freedesktop/login1",
    )

    bus.add_signal_receiver(
        handle_jobnew,
        dbus_interface="org.freedesktop.systemd1.Manager",
        signal_name="JobNew",
    )

    log_to_syslog("event handlers added")
    dbus_handlers_ready.set()

    loop = GLib.MainLoop()
    try:
        loop.run()
    finally:
        _release_shutdown_inhibitor()


def save_boot_splash():
    try:
        oled.save_boot_splash(Image.open(IMAGE_DIR + "/booting.png"))
        oled.save_boot_splash(
            Image.open(IMAGE_DIR + "/fpms-failed.png"), oled.boot_splash.FAILED_FILE
        )
    except OSError as exc:
        log_to_syslog(f"Boot splash not saved: {exc}", syslog.LOG_WARNING)


def read_value(section, key, default_value):
    config = configparser.ConfigParser()
    config.read(FPMS_CONF_FILE)

    if config.has_section(section) and config.has_option(section, key):
        value = config.get(section, key)
        return value
    else:
        return default_value


def save_value(section, key, new_value):
    config = configparser.ConfigParser()
    config.read(FPMS_CONF_FILE)

    if not config.has_section(section):
        config.add_section(section)

    config.set(section, key, new_value)

    with open(FPMS_CONF_FILE, "w") as f:
        config.write(f)


running: bool = False


def main():
    dbus_thread = threading.Thread(target=run_dbus_loop)
    dbus_thread.daemon = True
    dbus_thread.start()
    log_to_syslog("fpms starting after dbus thread setup")

    global g_vars
    global running

    def authors():
        authors = os.path.realpath(os.path.join(os.getcwd(), "AUTHORS.md"))
        if not os.path.isfile(authors):
            print(authors)
            return ""
        else:
            with open(authors) as f:
                return "\n".join(
                    filter(
                        None,
                        [
                            line if line.startswith("*") else ""
                            for line in f.read().splitlines()
                        ],
                    )
                )

    def usage():
        return """
usage: fpms [-a] [-h] [-e] [-v]

wlanpi-fpms drives the Front Panel Menu System on the WLAN Pi

optional options:
  -a                print authors
  -e                emulate buttons from keyboard; the menu is shown as
                    terminal text only when no ST7735/SSD1351 display is
                    present (on real hardware this drives that screen)
  -h                show this message and exit
  -v                show module version and exit
        """

    try:
        opts, _args = getopt.getopt(
            sys.argv[1:], ":ahev", ["authors", "help", "emulate-buttons", "version"]
        )
    except getopt.GetoptError as error:
        print(f"{error} ... ")
        print(usage())
        sys.exit(2)

    emulate = False

    for opt, _arg in opts:
        if opt in ["-e", "--emulate-buttons"]:
            emulate = True
        elif opt in ("-a", "--authors"):
            print(authors())
            sys.exit()
        elif opt in ("-h", "--help"):
            print(usage())
            sys.exit()
        elif opt in ("-v", "--version"):
            print(f"{__title__} {__version__}")
            sys.exit()
        else:
            raise AssertionError("unhandled option")

    # ponytail: gpio contention is the proxy for "another instance owns the
    # display/buttons"; it won't catch a non-fpms holder of the display only.
    # Add an explicit lock file if that case ever matters.
    button_request: Any = None
    if os.path.exists(GPIO_CHIP):
        line_setting = gpiod.LineSettings(
            bias=Bias.PULL_UP,
            edge_detection=Edge.FALLING,
            debounce_period=timedelta(microseconds=10),
        )
        lines = dict.fromkeys(BUTTONS_PINS.values(), line_setting)
        try:
            button_request = gpiod.request_lines(GPIO_CHIP, lines)
        except OSError:
            print(
                "fpms: another fpms instance is using the display/buttons. "
                "Stop it first (e.g. 'sudo systemctl stop wlanpi-fpms').",
                file=sys.stderr,
            )
            sys.exit(1)

    g_vars["display_orientation"] = read_value(
        "display", "orientation", DISPLAY_ORIENTATION_NORMAL
    )
    oled.orientation = g_vars["display_orientation"]
    oled.select_device()
    save_boot_splash()
    oled.init()

    g_vars["image"] = Image.new(DISPLAY_MODE, (PAGE_WIDTH, PAGE_HEIGHT))
    g_vars["draw"] = ImageDraw.Draw(g_vars["image"])
    g_vars["reboot_image"] = Image.open(IMAGE_DIR + "/reboot.png").convert(DISPLAY_MODE)
    g_vars["shutdown_image"] = Image.open(IMAGE_DIR + "/shutdown.png").convert(
        DISPLAY_MODE
    )

    # Report ready only once a reboot can draw its screen: startup reboots
    # (wlanpi-config-at-startup) wait for multi-user.target, which waits for this.
    # Without D-Bus, report ready anyway: a menu with no reboot screen beats
    # systemd killing fpms at TimeoutStartSec.
    if not dbus_handlers_ready.wait(timeout=20):
        log_to_syslog(
            "D-Bus handlers not ready; reboots started outside fpms show no screen",
            syslog.LOG_WARNING,
        )
    sd_notify_ready()

    env_utils = EnvUtils()
    g_vars["current_mode"] = env_utils.get_mode(MODE_FILE)

    g_vars["wlanpi_ver"] = env_utils.get_image_ver(WLANPI_IMAGE_FILE)

    profiler = Profiler(g_vars)
    g_vars["profiler_last_profile_date"] = profiler.profiler_last_profile_date()
    g_vars["profiler_beaconing"] = profiler.profiler_beaconing()

    timezone = TimeZone(g_vars)
    timezones_available = timezone.get_timezones_menu_format()

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

    def show_reachability():
        utils_obj = Utils(g_vars)
        utils_obj.show_reachability(g_vars)

    def show_speedtest():
        utils_obj = Utils(g_vars)
        utils_obj.show_speedtest(g_vars)

    def show_ruckus_test():
        utils_obj = CloudUtils(g_vars)
        utils_obj.test_ruckus_cloud(g_vars)

    def show_meraki_test():
        utils_obj = CloudUtils(g_vars)
        utils_obj.test_meraki_cloud(g_vars)

    def show_mist_test():
        utils_obj = CloudUtils(g_vars)
        utils_obj.test_mist_cloud(g_vars)

    def show_aruba_test():
        utils_obj = CloudUtils(g_vars)
        utils_obj.test_aruba_cloud(g_vars)

    def show_extreme_test():
        utils_obj = CloudUtils(g_vars)
        utils_obj.test_extreme_cloud(g_vars)

    def show_arista_test():
        utils_obj = CloudUtils(g_vars)
        utils_obj.test_arista_cloud(g_vars)

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

    def profiler_start_5ghz_unii1():
        app_obj = Profiler(g_vars)
        app_obj.profiler_start_5ghz_unii1(g_vars)

    def profiler_start_5ghz_unii3():
        app_obj = Profiler(g_vars)
        app_obj.profiler_start_5ghz_unii3(g_vars)

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

    def set_reg_domain(domain):
        def action():
            if RegDomain(g_vars).set_reg_domain(g_vars, domain):
                Button(g_vars, menu).shortcut(
                    g_vars,
                    menu,
                    create_shortcut(
                        menu, ["System", "Settings", "RF Domain", "Show Domain"]
                    ),
                )

        return action

    def toggle_display_orientation():
        if g_vars["display_orientation"] == DISPLAY_ORIENTATION_NORMAL:
            g_vars["display_orientation"] = DISPLAY_ORIENTATION_FLIPPED
        else:
            g_vars["display_orientation"] = DISPLAY_ORIENTATION_NORMAL
        oled.orientation = g_vars["display_orientation"]
        save_value("display", "orientation", g_vars["display_orientation"])
        save_boot_splash()

    def rotate_display():
        toggle_display_orientation()
        g_vars["sig_fired"] = True
        menu_left()
        g_vars["sig_fired"] = False

    def show_date():
        system_obj = System(g_vars)
        system_obj.show_date(g_vars)

    def set_time_zone_auto():
        system_obj = TimeZone(g_vars)
        system_obj.set_time_zone_auto(g_vars)

    def set_time_zone():
        g_vars["timezone_selected"] = (
            timezones_available[g_vars["current_menu_location"][5]]["country"]
            + "/"
            + timezones_available[g_vars["current_menu_location"][5]]["timezones"][
                g_vars["current_menu_location"][6]
            ]
        )

        system_obj = TimeZone(g_vars)
        system_obj.set_time_zone_from_gvars(g_vars)

    def show_about():
        system_obj = System(g_vars)
        system_obj.show_about(g_vars)

    def show_help():
        system_obj = System(g_vars)
        system_obj.show_help(g_vars)

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
            create_shortcut(menu, ["Utils", "Reachability"]),
            create_shortcut(menu, ["Network", "LLDP Neighbour"]),
            create_shortcut(menu, ["Network", "Eth0 IP Config"]),
        ]

        option_selected = g_vars["option_selected"]

        option_index = 0
        option_found = False

        if g_vars["display_state"] == "page":
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
        toggle_display_orientation()
        if g_vars["display_state"] == "page":
            if isinstance(g_vars["option_selected"], types.FunctionType):
                g_vars["option_selected"]()
        else:
            page_obj = Page(g_vars)
            page_obj.draw_page(g_vars, menu)

    def menu_key3():
        reboot_shortcut = create_shortcut(menu, ["System", "Reboot"])
        shutdown_shortcut = create_shortcut(menu, ["System", "Shutdown"])

        next_shortcut = reboot_shortcut
        if g_vars["current_menu_location"][:-1] == reboot_shortcut:
            next_shortcut = shutdown_shortcut

        button_obj = Button(g_vars, menu)
        button_obj.shortcut(g_vars, menu, next_shortcut)

    def create_shortcut(menu, path, location=None):
        if isinstance(menu, types.FunctionType):
            if len(path) > 0:
                raise Exception("invalid path")
            return [menu]

        if len(path) > 0:
            index = 0
            for item in menu:
                if item["name"] == path[0]:
                    return [index, *create_shortcut(item["action"], path[1:], location)]
                index += 1

        return []

    for timezones_country in timezones_available:
        g_vars["timezones_available"].append(
            {"name": timezones_country["country"], "action": []}
        )
        for timezone in timezones_country["timezones"]:
            g_vars["timezones_available"][-1]["action"].append(
                {"name": timezone, "action": set_time_zone}
            )

    menu: list[dict[str, Any]] = [
        {
            "name": "Network",
            "action": [
                {"name": "Interfaces", "action": show_interfaces},
                {"name": "WLAN Interfaces", "action": show_wlan_interfaces},
                {"name": "Eth0 IP Config", "action": show_eth0_ipconfig},
                {"name": "Eth0 VLAN", "action": show_vlan},
                {"name": "LLDP Neighbour", "action": show_lldp_neighbour},
                {"name": "CDP Neighbour", "action": show_cdp_neighbour},
                {"name": "Public IPv4", "action": show_publicip},
                {"name": "Public IPv6", "action": show_publicip6},
            ],
        },
        {
            "name": "Bluetooth",
            "action": [
                {"name": "Status", "action": bluetooth_status},
                {"name": "Turn On", "action": bluetooth_on},
                {"name": "Turn Off", "action": bluetooth_off},
                {"name": "Pair Device", "action": bluetooth_pair},
            ],
        },
        {
            "name": "Utils",
            "action": [
                {"name": "Reachability", "action": show_reachability},
                {
                    "name": "Speedtest",
                    "action": [
                        {"name": "Run Test", "action": show_speedtest},
                    ],
                },
                {
                    "name": "Cloud Tests",
                    "action": [
                        {"name": "Arista CV-CUE", "action": show_arista_test},
                        {"name": "Aruba Central", "action": show_aruba_test},
                        {"name": "ExtremeCloud IQ", "action": show_extreme_test},
                        {"name": "Meraki Cloud", "action": show_meraki_test},
                        {"name": "Mist Cloud", "action": show_mist_test},
                        {"name": "RUCKUS Cloud", "action": show_ruckus_test},
                    ],
                },
                {
                    "name": "Port Blinker",
                    "action": [
                        {"name": "Start", "action": show_blinker},
                        {"name": "Stop", "action": stop_blinker},
                    ],
                },
                {"name": "SSID/Passphrase", "action": show_ssid_passphrase},
                {"name": "USB Devices", "action": show_usb},
                {"name": "UFW Ports", "action": show_ufw},
            ],
        },
        {
            "name": "Apps",
            "action": [
                {
                    "name": "Kismet",
                    "action": [
                        {"name": "Start", "action": kismet_start},
                        {"name": "Stop", "action": kismet_stop},
                    ],
                },
                {
                    "name": "Profiler",
                    "action": [
                        {"name": "Status", "action": profiler_status},
                        {"name": "Stop", "action": profiler_stop},
                        {"name": "Start", "action": profiler_start},
                        {
                            "name": "Start Other",
                            "action": [
                                {
                                    "name": "Start 2.4 GHz",
                                    "action": profiler_start_2dot4ghz,
                                },
                                {
                                    "name": "Start 5 GHz 36",
                                    "action": profiler_start_5ghz_unii1,
                                },
                                {
                                    "name": "Start 5 GHz 149",
                                    "action": profiler_start_5ghz_unii3,
                                },
                                {
                                    "name": "Start (no 11r)",
                                    "action": profiler_start_no11r,
                                },
                                {
                                    "name": "Start (no 11ax)",
                                    "action": profiler_start_no11ax,
                                },
                            ],
                        },
                        {
                            "name": "Purge Reports",
                            "action": [
                                {"name": "Confirm", "action": profiler_purge_reports},
                            ],
                        },
                        {
                            "name": "Purge Files",
                            "action": [
                                {"name": "Confirm", "action": profiler_purge_files},
                            ],
                        },
                    ],
                },
                {
                    "name": "Scanner",
                    "action": [
                        {"name": "Scan", "action": scanner_scan},
                        {"name": "Scan (no hidden)", "action": scanner_scan_nohidden},
                        {"name": "Scan to CSV", "action": scanner_scan_tofile_csv},
                        {
                            "name": "Scan to PCAP",
                            "action": [
                                {
                                    "name": "Start",
                                    "action": scanner_scan_tofile_pcap_start,
                                },
                                {
                                    "name": "Stop",
                                    "action": scanner_scan_tofile_pcap_stop,
                                },
                            ],
                        },
                    ],
                },
            ],
        },
        {
            "name": "System",
            "action": [
                {"name": "About", "action": show_about},
                {"name": "Help", "action": show_help},
                {"name": "Summary", "action": show_summary},
                {"name": "Battery", "action": show_battery},
                {
                    "name": "Settings",
                    "action": [
                        {
                            "name": "Date & Time",
                            "action": [
                                {"name": "Show Time & Zone", "action": show_date},
                                {
                                    "name": "Set Timezone",
                                    "action": [
                                        {"name": "Auto", "action": set_time_zone_auto},
                                        {
                                            "name": "Manual",
                                            "action": g_vars["timezones_available"],
                                        },
                                    ],
                                },
                            ],
                        },
                        {
                            "name": "RF Domain",
                            "action": [
                                {"name": "Show Domain", "action": show_reg_domain},
                                {
                                    "name": "Set Domain US",
                                    "action": [
                                        {
                                            "name": "Confirm",
                                            "action": set_reg_domain("US"),
                                        },
                                    ],
                                },
                                {
                                    "name": "Set Domain AU",
                                    "action": [
                                        {
                                            "name": "Confirm",
                                            "action": set_reg_domain("AU"),
                                        },
                                    ],
                                },
                                {
                                    "name": "Set Domain BR",
                                    "action": [
                                        {
                                            "name": "Confirm",
                                            "action": set_reg_domain("BR"),
                                        },
                                    ],
                                },
                                {
                                    "name": "Set Domain CA",
                                    "action": [
                                        {
                                            "name": "Confirm",
                                            "action": set_reg_domain("CA"),
                                        },
                                    ],
                                },
                                {
                                    "name": "Set Domain CZ",
                                    "action": [
                                        {
                                            "name": "Confirm",
                                            "action": set_reg_domain("CZ"),
                                        },
                                    ],
                                },
                                {
                                    "name": "Set Domain DE",
                                    "action": [
                                        {
                                            "name": "Confirm",
                                            "action": set_reg_domain("DE"),
                                        },
                                    ],
                                },
                                {
                                    "name": "Set Domain FR",
                                    "action": [
                                        {
                                            "name": "Confirm",
                                            "action": set_reg_domain("FR"),
                                        },
                                    ],
                                },
                                {
                                    "name": "Set Domain GB",
                                    "action": [
                                        {
                                            "name": "Confirm",
                                            "action": set_reg_domain("GB"),
                                        },
                                    ],
                                },
                                {
                                    "name": "Set Domain NL",
                                    "action": [
                                        {
                                            "name": "Confirm",
                                            "action": set_reg_domain("NL"),
                                        },
                                    ],
                                },
                                {
                                    "name": "Set Domain NO",
                                    "action": [
                                        {
                                            "name": "Confirm",
                                            "action": set_reg_domain("NO"),
                                        },
                                    ],
                                },
                            ],
                        },
                        {"name": "Rotate Display", "action": rotate_display},
                    ],
                },
                {
                    "name": "Reboot",
                    "action": [
                        {"name": "Confirm", "action": reboot},
                    ],
                },
                {
                    "name": "Shutdown",
                    "action": [
                        {"name": "Confirm", "action": shutdown},
                    ],
                },
            ],
        },
    ]

    if g_vars["current_mode"] == "hotspot":
        g_vars["home_page_name"] = "Hotspot"

    if g_vars["current_mode"] == "wiperf":
        g_vars["home_page_name"] = "Wiperf"

    if g_vars["current_mode"] == "server":
        g_vars["home_page_name"] = "Server"

    if g_vars["current_mode"] == "bridge":
        g_vars["home_page_name"] = "Bridge"

    if g_vars["current_mode"] == "classic":
        for item in menu:
            if item["name"] == "Utils":
                for action in item["action"]:
                    if action["name"] == "SSID/Passphrase":
                        item["action"].remove(action)
                        break
    else:
        for item in menu:
            if item["name"] == "Apps":
                menu.remove(item)

    def button_press(gpio_pin, g_vars=g_vars):
        DOWN_KEY = BUTTONS_PINS["down"]
        UP_KEY = BUTTONS_PINS["up"]
        RIGHT_KEY = BUTTONS_PINS["right"]
        LEFT_KEY = BUTTONS_PINS["left"]
        CENTER_KEY = BUTTONS_PINS["center"]
        KEY1 = None
        KEY2 = None
        KEY3 = None

        if "key1" in BUTTONS_PINS:
            KEY1 = BUTTONS_PINS["key1"]

        if "key2" in BUTTONS_PINS:
            KEY2 = BUTTONS_PINS["key2"]

        if "key3" in BUTTONS_PINS:
            KEY3 = BUTTONS_PINS["key3"]

        if g_vars["disable_keys"]:
            return

        if g_vars["sig_fired"]:
            return

        g_vars["pageSleepCountdown"] = PAGE_SLEEP

        g_vars["start_up"] = False

        if g_vars["drawing_in_progress"] or g_vars["shutdown_in_progress"]:
            return

        g_vars["button_press_count"] += 1

        if g_vars["screen_cleared"]:
            wakeup_screen()
            return

        if gpio_pin == DOWN_KEY:
            g_vars["sig_fired"] = True
            menu_down()
            g_vars["sig_fired"] = False
            return

        if gpio_pin == UP_KEY:
            g_vars["sig_fired"] = True
            menu_up()
            g_vars["sig_fired"] = False
            return

        if gpio_pin == RIGHT_KEY:
            g_vars["sig_fired"] = True
            menu_right()
            g_vars["sig_fired"] = False
            return

        if gpio_pin == LEFT_KEY:
            g_vars["sig_fired"] = True
            menu_left()
            g_vars["sig_fired"] = False
            return

        if gpio_pin == CENTER_KEY:
            g_vars["sig_fired"] = True
            menu_center()
            g_vars["sig_fired"] = False
            return

        if gpio_pin == KEY1:
            g_vars["sig_fired"] = True
            menu_key1()
            g_vars["sig_fired"] = False
            return

        if gpio_pin == KEY2:
            g_vars["sig_fired"] = True
            menu_key2()
            g_vars["sig_fired"] = False
            return

        if gpio_pin == KEY3:
            g_vars["sig_fired"] = True
            menu_key3()
            g_vars["sig_fired"] = False
            return

    """
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
    """

    splash_screen_images = [
        IMAGE_DIR + "/wlanpi0.png",
        IMAGE_DIR + "/wlanpi1.png",
        IMAGE_DIR + "/wlanpi2.png",
        IMAGE_DIR + "/wlanpi3.png",
        IMAGE_DIR + "/wlanpi4.png",
    ]

    for image in splash_screen_images:
        img = Image.open(image).convert(DISPLAY_MODE)
        oled.drawImage(img)
        time.sleep(0.100)

    time.sleep(2)

    def up_key():
        button_press(BUTTONS_PINS["up"], g_vars)

    def down_key():
        button_press(BUTTONS_PINS["down"], g_vars)

    def left_key():
        button_press(BUTTONS_PINS["left"], g_vars)

    def right_key():
        button_press(BUTTONS_PINS["right"], g_vars)

    def center_key():
        button_press(BUTTONS_PINS["center"], g_vars)

    def key_1():
        button_press(BUTTONS_PINS["key1"], g_vars)

    def key_2():
        button_press(BUTTONS_PINS["key2"], g_vars)

    def key_3():
        button_press(BUTTONS_PINS["key3"], g_vars)

    def monitor_buttons():
        with button_request as request:
            while True:
                request.wait_edge_events(1)
                events = request.read_edge_events()

                for event in events:
                    if g_vars["display_orientation"] == DISPLAY_ORIENTATION_FLIPPED:
                        if event.line_offset == BUTTONS_PINS["up"]:
                            down_key()
                        elif event.line_offset == BUTTONS_PINS["down"]:
                            up_key()
                        elif event.line_offset == BUTTONS_PINS["left"]:
                            right_key()
                        elif event.line_offset == BUTTONS_PINS["right"]:
                            left_key()
                        elif event.line_offset == BUTTONS_PINS["center"]:
                            center_key()
                        elif event.line_offset == BUTTONS_PINS["key1"]:
                            key_3()
                        elif event.line_offset == BUTTONS_PINS["key2"]:
                            key_2()
                        elif event.line_offset == BUTTONS_PINS["key3"]:
                            key_1()
                    else:
                        if event.line_offset == BUTTONS_PINS["up"]:
                            up_key()
                        elif event.line_offset == BUTTONS_PINS["down"]:
                            down_key()
                        elif event.line_offset == BUTTONS_PINS["left"]:
                            left_key()
                        elif event.line_offset == BUTTONS_PINS["right"]:
                            right_key()
                        elif event.line_offset == BUTTONS_PINS["center"]:
                            center_key()
                        elif event.line_offset == BUTTONS_PINS["key1"]:
                            key_1()
                        elif event.line_offset == BUTTONS_PINS["key2"]:
                            key_2()
                        elif event.line_offset == BUTTONS_PINS["key3"]:
                            key_3()

    if button_request is not None:
        m = threading.Thread(name="button-monitor", target=monitor_buttons)
        m.daemon = True
        m.start()
    else:
        log_to_syslog(
            f"No {GPIO_CHIP} found; hardware buttons unavailable (use -e for keyboard emulation)"
        )

    button_key1_present = "key1" in BUTTONS_PINS
    button_key2_present = "key2" in BUTTONS_PINS
    button_key3_present = "key3" in BUTTONS_PINS

    running = True

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

            if char == "k" or char == "K":
                running = False
                os._exit(0)

            if char == "g" or char == "G":
                capture_screen()

            if char == "8" or char == "w":
                up_key()

            if char == "2" or char == "x":
                down_key()

            if char == "4" or char == "a":
                left_key()

            if char == "6" or char == "d":
                right_key()

            if char == "5" or char == "s":
                center_key()

            if button_key1_present:
                if char == "*" or char == "i":
                    key_1()

            if button_key2_present:
                if char == "-" or char == "o":
                    key_2()

            if button_key3_present:
                if char == "+" or char == "p":
                    key_3()

    if emulate:
        hints = ["w/x/a/d/s: up/down/left/right/center", "g: screenshot   k: quit"]
        if button_key1_present and button_key2_present and button_key3_present:
            hints.append("i/o/p: key1/key2/key3")
        oled.set_hints(hints)
        print("\n".join(hints), flush=True)
        e = threading.Thread(name="button-emulator", target=emulate_buttons)
        e.daemon = True
        e.start()

    def capture_screen():
        g_vars["sig_fired"] = True
        screenshots_dir = "/home/wlanpi/screenshots"
        if not os.path.exists(screenshots_dir):
            os.makedirs(screenshots_dir)
        timestr = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")
        save_file = screenshots_dir + "/screenshot_" + timestr + ".png"
        g_vars["image"].save(save_file)
        print(save_file)
        g_vars["sig_fired"] = False

    def sleep_screen():
        oled.sleep()
        g_vars["screen_cleared"] = True

    def wakeup_screen():
        oled.wakeup()
        g_vars["screen_cleared"] = False
        g_vars["pageSleepCountdown"] = PAGE_SLEEP

    def check_eth():
        """
        Detects a change in the status of the Ethernet port and wakes up
        the screen if necessary
        """
        try:
            with open("/sys/class/net/eth0/carrier") as f:
                carrier = int(f.read().strip())
            if g_vars["eth_carrier_status"] != carrier:
                wakeup_screen()
            g_vars["eth_carrier_status"] = carrier
        except (OSError, ValueError):
            pass

    while running:
        try:
            check_eth()

            if (
                g_vars["shutdown_in_progress"]
                or g_vars["screen_cleared"]
                or g_vars["drawing_in_progress"]
                or g_vars["sig_fired"]
            ):
                time.sleep(2)
                continue

            if g_vars["display_state"] != "menu":
                if g_vars["start_up"]:
                    g_vars["option_selected"] = home_page

                if isinstance(g_vars["option_selected"], types.FunctionType):
                    g_vars["option_selected"]()

            else:
                if g_vars["button_press_count"] > g_vars["last_button_press_count"]:
                    page_obj = Page(g_vars)
                    page_obj.draw_page(g_vars, menu)

            if g_vars["pageSleepCountdown"] == 0 and not g_vars["screen_cleared"]:
                sleep_screen()

            if g_vars["pageSleepCountdown"] > 0:
                g_vars["pageSleepCountdown"] = g_vars["pageSleepCountdown"] - 1

            time.sleep(2)

        except KeyboardInterrupt:
            break
        except OSError as ex:
            print("Error " + str(ex))

        g_vars["last_button_press_count"] = g_vars["button_press_count"]

    """
    Discounted ideas

        1. Vary sleep timer for main while loop (e.g. longer for less frequently
           updating data) - doesn;t work as main while loop may be in middle of
           long sleep when button action taken, so screen refresh very long.

    """
