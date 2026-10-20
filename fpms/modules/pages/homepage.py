import os.path
import re
import subprocess
import threading
import time

import textfsm

import fpms.modules.wlanpi_oled as oled
from fpms.modules.apps.kismet import Kismet
from fpms.modules.apps.profiler import Profiler
from fpms.modules.apps.scanner import Scanner
from fpms.modules.battery import Battery
from fpms.modules.bluetooth import Bluetooth
from fpms.modules.constants import (
    ETHTOOL_FILE,
    FONTB10,
    FONTB11,
    FONTB12,
    FONTB13,
    ICONS,
    IFCONFIG_FILE,
    PAGE_WIDTH,
    PLATFORM,
    REACHABILITY_FILE,
    SMART_FONT,
    STATUS_BAR_HEIGHT,
    SYSTEM_BAR_HEIGHT,
    TINY_FONT,
)
from fpms.modules.env_utils import EnvUtils
from fpms.modules.network import IwInterface, iw_dev_outputs, netns_cmd
from fpms.modules.pages.display import Display
from fpms.modules.pages.simpletable import SimpleTable
from fpms.modules.themes import THEME


class HomePage:
    def __init__(self, g_vars):
        with open(
            os.path.realpath(
                os.path.join(os.getcwd(), "modules/templates/iw_dev.textfsm")
            )
        ) as f:
            self.iw_textfsm_template = textfsm.TextFSM(f)

        self.display_obj = Display(g_vars)

        self.simple_table_obj = SimpleTable(g_vars)

        self.scanner_obj = Scanner(g_vars)

        self.profiler_obj = Profiler(g_vars)

        self.kismet_obj = Kismet(g_vars)

        self.env_obj = EnvUtils()

        thread = threading.Thread(
            target=self.check_reachability, args=(g_vars,), daemon=True
        )
        thread.start()

    def wifi_client_count(self):
        """
        Get a count of connected clients when in hotspot mode
        """
        cmd = "sudo /sbin/iw dev wlan0 station dump | grep 'Station' | wc -l"

        try:
            client_count = subprocess.check_output(cmd, shell=True).decode().strip()
            return int(client_count)
        except subprocess.CalledProcessError:
            return -1

    def _get_iw_interfaces(self):
        """
        Return the parsed `iw dev` interfaces across the root and named
        network namespaces, computed at most once per HomePage instance
        (i.e. once per render).
        """
        if getattr(self, "_iw_interfaces", None) is None:
            interfaces = []
            for netns, iw_dev_output in iw_dev_outputs():
                self.iw_textfsm_template.Reset()
                for row in self.iw_textfsm_template.ParseText(iw_dev_output.strip()):
                    phy, name, iftype = row
                    interfaces.append(IwInterface(phy, name, iftype, netns))
            self._iw_interfaces: list[IwInterface] | None = interfaces
        return self._iw_interfaces

    def _get_bt_power(self, g_vars):
        """
        Return whether the Bluetooth adapter is powered, computed at most once
        per HomePage instance (i.e. once per render).
        """
        if getattr(self, "_bt_power", None) is None:
            self._bt_power = Bluetooth(g_vars).bluetooth_power()
        return self._bt_power

    def check_wlan(self):
        """
        Returns true if there's at least one WLAN interface present.
        """
        try:
            return len(self._get_iw_interfaces()) > 0
        except Exception as e:
            print(e)

        return False

    def check_reg_domain(self):
        """
        Returns true if the reg. domain is set, false otherwise.
        """
        reg_domain_cmd = '/usr/bin/wlanpi-reg-domain get | grep "XX"'
        try:
            subprocess.run(
                reg_domain_cmd,
                shell=True,
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                check=True,
            )
            return False
        except subprocess.CalledProcessError:
            return True

    def check_port_blinker(self, g_vars):
        """
        Returns true if port blinker is active, false otherwise.
        """
        if g_vars["blinker_status"]:
            return True
        else:
            return False

    def check_wiperf_status(self):
        """
        Read the wiperf status file for visual status indication
        when in iperf mode
        """

        status_file = "/tmp/wiperf_status.txt"
        if os.path.exists(status_file):
            try:
                statusf = open(status_file)
                msg = statusf.readline()
            except Exception:
                return ""

            return f" ({msg})"
        else:
            return "15 Mbps/30 Mbps"

    def check_reachability(self, g_vars):
        address_set = self.if_addresses()
        if g_vars["eth_last_known_address_set"] != address_set:
            g_vars["eth_last_known_address_set"] = address_set
            g_vars["eth_last_reachability_test"] = 0

        last_reachability_test = g_vars["eth_last_reachability_test"]
        if last_reachability_test > 0:
            g_vars["eth_last_reachability_test"] = last_reachability_test - 1
        else:
            g_vars["eth_last_reachability_test"] = 30

            reachability_cmd = (
                "sudo " + REACHABILITY_FILE + " | grep -i 'browse google' | grep OK"
            )

            try:
                subprocess.run(
                    reachability_cmd,
                    shell=True,
                    stderr=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    check=True,
                )
                g_vars["eth_last_reachability_result"] = True
            except subprocess.CalledProcessError:
                g_vars["eth_last_reachability_result"] = False

    def if_addresses(self):
        """
        Returns the set of IP addresses set on the device (for all interfaces)
        """
        cmd = "ifconfig | grep -E 'inet[6]?' | awk '{ print $2 }'"
        try:
            output = subprocess.check_output(cmd, shell=True).decode().strip().split()
            return set(output)
        except Exception:
            pass

        return set()

    def if_address(self, if_name):
        """
        Returns the IP address for the given interface
        """
        ip_addr = "No IP address"

        cmd = rf"ip addr show {if_name}  2>/dev/null | grep -Po 'inet \K[\d.]+' | head -n 1"
        try:
            output = subprocess.check_output(cmd, shell=True).decode().strip()
            if len(output) > 0:
                ip_addr = output
        except Exception:
            pass

        return ip_addr

    def if_wireless(self, if_name):
        """
        Returns True if the interface is a wireless interface, False otherwise.
        """

        try:
            subprocess.run(
                ["iw", "dev", if_name, "info"],
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                check=True,
            )
            return True
        except Exception:
            pass

        return False

    def if_link_status(self, if_name):
        """
        Returns the link status for the given interface
        """

        if self.if_wireless(if_name):
            return None

        status = None
        try:
            eth_info = subprocess.check_output(
                [ETHTOOL_FILE, if_name], stderr=subprocess.DEVNULL
            ).decode()
            speed_re = re.findall(r"Speed\: (.*\/s)", eth_info, re.MULTILINE)
            duplex_re = re.findall(r"Duplex\: (.*)", eth_info, re.MULTILINE)
            link_re = re.findall(r"Link detected\: (.*)", eth_info, re.MULTILINE)

            if link_re and link_re[0] == "no":
                status = "Link down"
            elif speed_re and duplex_re:
                status = f"{speed_re[0]} {duplex_re[0]}"

        except Exception:
            pass

        return status

    def home_page(self, g_vars, menu):
        self.home_page_pro(g_vars, menu)

    def home_page_pro(self, g_vars, menu):
        x = 0
        y = 0
        padding = 2

        self._iw_interfaces = None
        self._bt_power = None

        g_vars["drawing_in_progress"] = True
        g_vars["display_state"] = "page"
        canvas = g_vars["draw"]

        self.display_obj.clear_display(g_vars)

        if_name = "eth0"
        mode_name = PLATFORM
        mode = self.classic_mode

        if g_vars["current_mode"] == "hotspot":
            if_name = "wlan0"
            mode_name = "Hotspot"
            mode = self.hotspot_mode
        elif g_vars["current_mode"] == "wiperf":
            if_name = "wlan0"
            mode_name = "Wiperf"
            mode = self.wiperf_mode
        elif g_vars["current_mode"] == "server":
            if_name = "eth0"
            mode_name = "DHCP Server"
            mode = self.dhcp_server_mode
        elif g_vars["current_mode"] == "bridge":
            if_name = "usb0"
            mode_name = "Bridge"
            mode = self.bridge_mode

        system_bar_contents = self.env_obj.get_hostname()

        y += self.status_bar(g_vars)
        y += padding * 4

        display_alternate_title = False
        title = mode_name
        if g_vars["home_page_alternate"]:
            if g_vars["current_mode"] == "classic":
                if self.profiler_obj.profiler_beaconing():
                    display_alternate_title = True
                    title = self.profiler_obj.profiler_beaconing_ssid()
            else:
                display_alternate_title = True

        if len(title) > 21:
            title = title[0:19] + ".."

        if display_alternate_title:
            y -= 2
            canvas.text(
                (x + (PAGE_WIDTH - FONTB10.getbbox(title)[2]) / 2, y),
                title,
                font=FONTB10,
                fill=THEME.text_highlighted_color.value,
            )
            y += 10 + padding * 2
        else:
            canvas.text(
                (x + (PAGE_WIDTH - FONTB13.getbbox(title)[2]) / 2, y + padding),
                title,
                font=FONTB13,
                fill=THEME.text_highlighted_color.value,
            )
            y += 14 + padding * 2

        mode(g_vars, x=x, y=y, padding=padding)

        alert_bar_contents = None
        alert_bar_error = False
        if not self.check_wlan():
            alert_bar_contents = "NO WI-FI ADAPTER"
            alert_bar_error = True
        elif not self.check_reg_domain():
            alert_bar_contents = "REG. DOMAIN NOT SET"
            alert_bar_error = True
        elif self.check_port_blinker(g_vars):
            if not display_alternate_title:
                alert_bar_contents = "PORT BLINKER ACTIVE"
        elif self.scanner_obj.scanner_active(g_vars):
            if not display_alternate_title:
                alert_bar_contents = "SCANNER ACTIVE"
        elif self.profiler_obj.profiler_beaconing():
            if not display_alternate_title:
                alert_bar_contents = "PROFILER ACTIVE"
        elif self.kismet_obj.kismet_status():
            if not display_alternate_title:
                alert_bar_contents = "KISMET ACTIVE"

        self.alert_bar(
            g_vars,
            alert_bar_contents,
            x=0,
            y=PAGE_WIDTH - SYSTEM_BAR_HEIGHT - SYSTEM_BAR_HEIGHT,
            error=alert_bar_error,
        )

        self.system_bar(
            g_vars, system_bar_contents, x=0, y=PAGE_WIDTH - SYSTEM_BAR_HEIGHT - 1
        )

        if g_vars["home_page_alternate"]:
            self.profiler_obj.profiler_check_new_profile(g_vars)

        home_lines = []

        status = time.strftime("%H:%M")
        try:
            battery = Battery(g_vars)
            if battery.battery_present():
                status += f" \u26a1{battery.battery_charge():.0f}%"
        except Exception:
            pass
        try:
            if self._get_bt_power(g_vars):
                status += " \U0001f3e7"
        except Exception:
            pass
        if g_vars["eth_last_reachability_result"]:
            status += " \u2600"
        home_lines.append(status)

        addr = self.if_address(if_name)
        if addr and addr.lower() != "no ip address":
            home_lines.append(f"{if_name}: {addr}")
        link = self.if_link_status(if_name)
        if link:
            home_lines.append(link)

        if alert_bar_contents:
            home_lines.append(alert_bar_contents)

        home_lines.append(system_bar_contents)

        home_title = title if title else g_vars["current_mode"].title()
        oled.render_text(home_title, home_lines)
        oled.drawImage(g_vars["image"])
        g_vars["drawing_in_progress"] = False

    def iface_details(self, g_vars, if_name, x=0, y=0, padding=2):
        """
        Displays the IP address and link status details for the given interface
        """

        canvas = g_vars["draw"]
        offset = 0

        addr = self.if_address(if_name)
        link_status = self.if_link_status(if_name)
        if addr is not None:
            text_color = (
                THEME.text_color.value
                if addr.lower() != "no ip address"
                else THEME.text_important_color.value
            )
            canvas.text(
                (x + (PAGE_WIDTH - FONTB12.getbbox(addr)[2]) / 2, y + padding + offset),
                addr,
                font=FONTB12,
                fill=text_color,
            )
            offset += 13
        if link_status is not None:
            canvas.text(
                (
                    x + (PAGE_WIDTH - SMART_FONT.getbbox(link_status)[2]) / 2,
                    y + padding + offset,
                ),
                link_status,
                font=SMART_FONT,
                fill=THEME.text_secondary_color.value,
            )
            offset += 11

        return offset + 8

    def iface_summary(self, g_vars, if_name, label, x=0, y=0, padding=2):
        """
        Displays a custom label and IP address for the given interface
        """

        canvas = g_vars["draw"]
        addr = self.if_address(if_name)
        if addr.lower() != "no ip address":
            info = f"{label}: {addr}"
            canvas.text(
                (x + (PAGE_WIDTH - SMART_FONT.getbbox(info)[2]) / 2, y),
                info,
                font=SMART_FONT,
                fill=THEME.text_tertiary_color.value,
            )
            return 11

        return 0

    def classic_mode(self, g_vars, x=0, y=0, padding=2):
        if not self.profiler_obj.profiler_beaconing():
            g_vars["home_page_alternate"] = False

        if g_vars["home_page_alternate"]:
            self.profiler_qrcode(g_vars, x, y)
        else:
            y += self.iface_details(g_vars, "eth0", x=x, y=y, padding=padding)

            y += self.iface_summary(g_vars, "eth1", "ETH1", x=x, y=y)

            y += self.iface_summary(g_vars, "usb1", "USB1", x=x, y=y)

            pan = self.if_address("pan0")
            if pan.lower() != "no ip address":
                if self._get_bt_power(g_vars):
                    paired_devices = Bluetooth(g_vars).bluetooth_paired_devices()
                    if paired_devices is not None:
                        y += self.iface_summary(g_vars, "pan0", "PAN", x=x, y=y)

            y += self.iface_summary(g_vars, "usb0", "OTG", x=x, y=y)

    def hotspot_mode(self, g_vars, x=0, y=0, padding=2):
        if g_vars["home_page_alternate"]:
            self.wifi_qrcode(g_vars, x, y)
        else:
            canvas = g_vars["draw"]
            y += self.iface_details(g_vars, "wlan0", x=x, y=y, padding=padding)

            client_count = self.wifi_client_count()
            if client_count >= 0:
                clients = str(client_count) + (
                    " client" if client_count == 1 else " clients"
                )
                canvas.text(
                    (x + (PAGE_WIDTH - SMART_FONT.getbbox(clients)[2]) / 2, y),
                    clients,
                    font=SMART_FONT,
                    fill=THEME.text_secondary_color.value,
                )
                y += 18

            y += self.iface_summary(g_vars, "eth0", "LAN", x=x, y=y)

            y += self.iface_summary(g_vars, "usb0", "OTG", x=x, y=y)

    def bridge_mode(self, g_vars, x=0, y=0, padding=2):
        y += self.iface_details(g_vars, "eth0", x=x, y=y, padding=padding)

        y += self.iface_summary(g_vars, "usb0", "OTG", x=x, y=y)

    def wiperf_mode(self, g_vars, x=0, y=0, padding=2):
        canvas = g_vars["draw"]
        y += self.iface_details(g_vars, "wlan0", x=x, y=y, padding=padding)
        y += 12
        status = self.check_wiperf_status()
        canvas.text(
            (x + (PAGE_WIDTH - SMART_FONT.getbbox(status)[2]) / 2, y),
            status,
            font=SMART_FONT,
            fill=THEME.text_tertiary_color.value,
        )

    def dhcp_server_mode(self, g_vars, x=0, y=0, padding=2):
        if g_vars["home_page_alternate"]:
            self.wifi_qrcode(g_vars, x, y)
        else:
            y += self.iface_details(g_vars, "eth0", x=x, y=y, padding=padding)

            y += self.iface_summary(g_vars, "usb0", "OTG", x=x, y=y)

    def profiler_qrcode(self, g_vars, x, y):
        """
        Displays the profiler QR code
        """
        qrcode_path = self.profiler_obj.profiler_qrcode()
        if qrcode_path is not None:
            self.display_obj.stamp_qrcode(
                g_vars,
                qrcode_path,
                center_vertically=False,
                y=y + 2,
                draw_immediately=False,
            )

    def wifi_qrcode(self, g_vars, x, y):
        """
        Displays the Wi-Fi QR code
        """
        qrcode_path = self.env_obj.get_wifi_qrcode_for_hostapd()
        if qrcode_path is not None:
            self.display_obj.stamp_qrcode(
                g_vars,
                qrcode_path,
                center_vertically=False,
                y=y,
                draw_immediately=False,
            )

    def battery_indicator(self, g_vars, x, y, width, height):
        """
        Displays a battery indicator that shows charge level and power status
        """
        battery = Battery(g_vars)

        if not battery.battery_present():
            return False

        canvas = g_vars["draw"]
        bx = x + 3
        by = y + 2

        battery_indicator_width = 16
        battery_indicator_height = 8
        canvas.rounded_rectangle(
            (bx, by, bx + battery_indicator_width, by + battery_indicator_height),
            radius=1,
            outline=THEME.status_bar_foreground.value,
        )

        bx = bx + battery_indicator_width
        by = by + 3
        canvas.rectangle(
            (bx, by, bx + 1, by + 2), fill=THEME.status_bar_foreground.value
        )

        status = battery.battery_status()
        charge = battery.battery_charge()

        if charge > 0:
            bx = x + 2
            by = y + 2
            fill_color = THEME.status_bar_foreground.value

            if status == "charging":
                fill_color = THEME.status_bar_battery_full.value
            elif charge <= 25:
                fill_color = THEME.status_bar_battery_low.value
            elif charge >= 100:
                if status == "not charging":
                    fill_color = THEME.status_bar_battery_full.value

            canvas.rectangle(
                (
                    bx + 2,
                    by + 2,
                    bx + ((battery_indicator_width - 2) * charge / 100),
                    by + battery_indicator_height - 2,
                ),
                fill=fill_color,
            )

        if status == "charging":
            xy = [
                (bx + battery_indicator_width / 2 + 1, by - 2),
                (
                    bx + battery_indicator_width / 2 - 4,
                    by + battery_indicator_height / 2 + 1,
                ),
                (
                    bx + battery_indicator_width / 2 - 1,
                    by + battery_indicator_height / 2 + 1,
                ),
                (
                    bx + battery_indicator_width / 2 - 1,
                    by + battery_indicator_height + 2,
                ),
                (
                    bx + battery_indicator_width / 2 + 4,
                    by + battery_indicator_height / 2 - 1,
                ),
                (
                    bx + battery_indicator_width / 2 + 1,
                    by + battery_indicator_height / 2 - 1,
                ),
            ]
            canvas.polygon(
                xy,
                fill=THEME.status_bar_foreground.value,
                outline=THEME.status_bar_background.value,
            )

        return True

    def temperature_indicator(self, g_vars, x, y, width, height):
        """
        Displays a system temperature indicator
        """

        temp_high = 80
        temp_med = 75
        temp_low = 70

        temp: float = 0
        try:
            temp = int(open("/sys/class/thermal/thermal_zone0/temp").read())
        except Exception:
            temp = 0

        if temp > 1000:
            temp = temp / 1000

        if temp < temp_low:
            return False

        canvas = g_vars["draw"]

        if temp >= temp_high:
            temp_color = THEME.status_bar_temp_high.value
        elif temp >= temp_med:
            temp_color = THEME.status_bar_temp_med.value
        elif temp >= temp_low:
            temp_color = THEME.status_bar_temp_low.value
        else:
            temp_color = THEME.status_bar_foreground.value

        x = x + (width - 6) / 2

        canvas.ellipse((x, y + 7, x + 6, y + 13), fill=temp_color)
        canvas.rounded_rectangle(
            (x + 2, y + 1, x + 4, y + 11),
            fill=THEME.status_bar_background.value,
            outline=temp_color,
            radius=1,
        )

        canvas.line((x + 6, y + 2, x + 7, y + 2), fill=temp_color)
        canvas.line((x + 6, y + 4, x + 7, y + 4), fill=temp_color)
        canvas.line((x + 6, y + 6, x + 7, y + 6), fill=temp_color)

        if temp >= temp_high:
            canvas.rounded_rectangle(
                (x + 2, y + 2, x + 4, y + 11), fill=temp_color, radius=1
            )
        elif temp >= temp_med:
            canvas.rounded_rectangle(
                (x + 2, y + 4, x + 4, y + 11), fill=temp_color, radius=1
            )
        elif temp >= temp_low:
            canvas.rounded_rectangle(
                (x + 2, y + 6, x + 4, y + 11), fill=temp_color, radius=1
            )

        return True

    def wifi_indicator(self, g_vars, interfaces, if_name, x, y, width, height):
        """
        Displays a wifi indicator for the given wifi interface
        """
        canvas = g_vars["draw"]
        status_up = False
        monitor_mode = False
        active = False

        for iface in interfaces:
            if iface.name == if_name:
                # phy index (phy indexes are unique across namespaces)
                phy = iface.phy

                try:
                    ifconfig_output = subprocess.check_output(
                        netns_cmd(iface.netns, [IFCONFIG_FILE, if_name]),
                        stderr=subprocess.DEVNULL,
                    ).decode()
                    status_up = "UP" in ifconfig_output
                except Exception:
                    pass

                for other_iface in interfaces:
                    if phy == other_iface.phy:
                        if other_iface.type == "monitor":
                            monitor_mode = True

                            try:
                                subprocess.run(
                                    f"ps aux 2>&1 | grep -v grep | grep -E 'tcpdump|dumpcap' | grep {other_iface.name}",
                                    shell=True,
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL,
                                    check=True,
                                )
                                active = True
                            except Exception:
                                pass

                if monitor_mode and not active:
                    if self.profiler_obj.profiler_interface() == if_name:
                        if self.profiler_obj.profiler_beaconing():
                            active = True

                fill_color = THEME.status_bar_foreground.value

                if active:
                    fill_color = THEME.status_bar_wifi_active.value

                if status_up or monitor_mode:
                    canvas.pieslice(
                        (x, y + 3, x + height, y + height + 3),
                        225,
                        315,
                        fill=fill_color,
                    )
                    if monitor_mode:
                        canvas.ellipse(
                            (
                                x + height / 2 - 3,
                                y + height / 2 - 2,
                                x + height / 2 + 3,
                                y + height / 2,
                            ),
                            fill=THEME.status_bar_background.value,
                        )
                        canvas.ellipse(
                            (
                                x + height / 2 - 1,
                                y + height / 2 - 2,
                                x + height / 2 + 1,
                                y + height / 2,
                            ),
                            fill=fill_color,
                        )
                else:
                    canvas.pieslice(
                        (x, y + 3, x + height, y + height + 3),
                        225,
                        315,
                        outline=fill_color,
                    )

                canvas.text(
                    (x + width / 2 + 3, y + height - 8),
                    if_name[-1],
                    font=TINY_FONT,
                    fill=fill_color,
                )

                return True

        return False

    def bluetooth_indicator(self, g_vars, x, y, width, height):
        """
        Displays a bluetooth icon if bluetooth is on
        """

        if self._get_bt_power(g_vars):
            bluetooth_icon = chr(0xF128)
            canvas = g_vars["draw"]
            x = x + (width - ICONS.getbbox(bluetooth_icon)[2]) / 2 + 1
            canvas.text(
                (x, y),
                bluetooth_icon,
                font=ICONS,
                fill=THEME.status_bar_foreground.value,
            )
            return True

        return False

    def reachability_indicator(self, g_vars, x, y, width, height):
        """
        Displays a 'world' icon if we can reach the Internet via the Ethernet interface
        """

        canvas = g_vars["draw"]
        canvas.ellipse(
            (x + 4, y + 2, x + height, y + height - 2),
            outline=THEME.status_bar_foreground.value,
        )
        canvas.ellipse(
            (x + 7, y + 2, x + height - 3, y + height - 2),
            outline=THEME.status_bar_foreground.value,
        )
        canvas.line(
            (x + 4, y + height / 2, x + height, y + height / 2),
            fill=THEME.status_bar_foreground.value,
        )

        if not g_vars["eth_last_reachability_result"]:
            canvas.line(
                (x + 3, y + 1, x + height, y + height - 2),
                fill=THEME.status_bar_foreground.value,
                width=2,
            )

        return True

    def status_bar(
        self, g_vars, x=0, y=0, padding=2, width=PAGE_WIDTH, height=STATUS_BAR_HEIGHT
    ):
        canvas = g_vars["draw"]

        current_time = time.strftime("%H:%M")
        current_time_width = FONTB11.getbbox(current_time)[2]
        canvas.rectangle((x, y, width, height), fill=THEME.status_bar_background.value)
        canvas.text(
            (x + padding + 2, y + 2),
            current_time,
            font=FONTB11,
            fill=THEME.status_bar_foreground.value,
        )

        x = width - 20
        fixed_indicator_width = 16

        if self.battery_indicator(g_vars, x - 4, y + 2, 24, height):
            x -= fixed_indicator_width + 4

        y += 1
        height -= 2

        if x > current_time_width:
            if self.temperature_indicator(g_vars, x, y, fixed_indicator_width, height):
                x -= fixed_indicator_width

        try:
            interfaces = self._get_iw_interfaces()

            if x > current_time_width:
                if self.wifi_indicator(
                    g_vars, interfaces, "wlan1", x, y, fixed_indicator_width, height
                ):
                    x -= fixed_indicator_width

            if x > current_time_width:
                if self.wifi_indicator(
                    g_vars, interfaces, "wlan0", x, y, fixed_indicator_width, height
                ):
                    x -= fixed_indicator_width

        except Exception as e:
            print(e)

        if x > current_time_width:
            if self.bluetooth_indicator(g_vars, x, y, fixed_indicator_width, height):
                x -= fixed_indicator_width

        if x > current_time_width:
            if self.reachability_indicator(g_vars, x, y, fixed_indicator_width, height):
                x -= fixed_indicator_width

        return height

    def alert_bar(
        self,
        g_vars,
        contents,
        x=0,
        y=0,
        padding=0,
        width=PAGE_WIDTH,
        height=SYSTEM_BAR_HEIGHT,
        error=False,
    ):
        if contents is not None:
            canvas = g_vars["draw"]

            foreground = THEME.alert_info_title_foreground.value
            background = THEME.alert_info_title_background.value
            if error:
                foreground = THEME.alert_error_title_foreground.value
                background = THEME.alert_error_title_background.value

            canvas.rectangle((x, y, width, y + height), fill=background)

            if len(contents) > 21:
                contents = contents[0:19] + ".."

            canvas.text(
                (x + (PAGE_WIDTH - FONTB10.getbbox(contents)[2]) / 2, y + padding),
                contents,
                font=FONTB10,
                fill=foreground,
            )

        return height

    def system_bar(
        self,
        g_vars,
        contents,
        x=0,
        y=0,
        padding=2,
        width=PAGE_WIDTH,
        height=SYSTEM_BAR_HEIGHT,
    ):
        canvas = g_vars["draw"]

        canvas.rectangle(
            (x, y, width, y + height), fill=THEME.system_bar_background.value
        )

        if contents is not None:
            if len(contents) > 21:
                contents = contents[0:19] + ".."

            canvas.text(
                (x + (PAGE_WIDTH - SMART_FONT.getbbox(contents)[2]) / 2, y + padding),
                contents,
                font=SMART_FONT,
                fill=THEME.system_bar_foreground.value,
            )

        return height
