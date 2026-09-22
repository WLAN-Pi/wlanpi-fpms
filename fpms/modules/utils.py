import json
import os
import os.path
import subprocess

from fpms.modules.constants import (
    BLINKER_FILE,
    REACHABILITY_FILE,
    UFW_FILE,
)
from fpms.modules.env_utils import EnvUtils
from fpms.modules.pages.alert import *
from fpms.modules.pages.pagedtable import *
from fpms.modules.pages.simpletable import *


class Utils:
    def __init__(self, g_vars):
        # create display object
        self.display_obj = Display(g_vars)

        # create simple table object to show dialog & results on display
        self.simple_table_obj = SimpleTable(g_vars)

        # create paged table
        self.paged_table_obj = PagedTable(g_vars)

        # create alert
        self.alert_obj = Alert(g_vars)

    def show_speedtest(self, g_vars):
        """
        Run LibreSpeed and format output to fit the OLED screen
        """
        # Has speedtest been run already?
        if not g_vars["result_cache"]:
            # ignore any more key presses as this could cause us issues
            g_vars["disable_keys"] = True
            g_vars["speedtest_result_text"] = None

            speedtest_bin = self.speedtest_cli_path()
            if speedtest_bin is None:
                self.alert_obj.display_alert_error(
                    g_vars, "Speedtest CLI not installed."
                )
                g_vars["disable_keys"] = False
                g_vars["result_cache"] = True
                return

            self.alert_obj.display_popup_alert(g_vars, "Running...")

            try:
                speedtest_output = subprocess.run(
                    [speedtest_bin, "--json", "--simple"],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=True,
                )
                speedtest_info = self.parse_librespeed_output(speedtest_output.stdout)
            except (subprocess.SubprocessError, ValueError):
                g_vars["speedtest_result_text"] = None
                g_vars["disable_keys"] = False
                g_vars["result_cache"] = True
                self.alert_obj.display_alert_error(g_vars, "Failed to run speedtest.")
                return

            g_vars["speedtest_result_text"] = speedtest_info

            g_vars["result_cache"] = True

        # re-enable front panel keys
        g_vars["disable_keys"] = False

        if g_vars["speedtest_result_text"] is None:
            self.alert_obj.display_alert_error(g_vars, "Failed to run speedtest.")
        else:
            self.simple_table_obj.display_simple_table(
                g_vars, g_vars["speedtest_result_text"], title="Speedtest"
            )

    @staticmethod
    def speedtest_cli_path():
        """Locate the LibreSpeed CLI installed by wlanpi-librespeed-cli."""
        path = "/usr/bin/librespeed-cli"
        return path if os.path.isfile(path) else None

    @staticmethod
    def parse_librespeed_output(output):
        """Return compact display lines from LibreSpeed JSON output."""
        for line in reversed(output.strip().splitlines()):
            if not line.lstrip().startswith("["):
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, list) and payload:
                result = payload[0]
                try:
                    ping = float(result["ping"])
                    download = float(result["download"])
                    upload = float(result["upload"])
                except (KeyError, TypeError, ValueError) as exc:
                    raise ValueError("speedtest result is incomplete") from exc
                lines = []
                ip_address = (result.get("client") or {}).get("ip")
                if ip_address:
                    lines.append(f"My IP: {ip_address}")
                lines.extend(
                    [
                        f"Ping: {ping:.2f} ms",
                        f"D: {download:.2f} Mbps",
                        f"U: {upload:.2f} Mbps",
                    ]
                )
                return lines
        raise ValueError("speedtest output did not contain JSON results")

    def show_blinker(self, g_vars):
        """
        Run Port Blinker on eth0 and identify switch port on the far end of the Ethernet cable
        ( *** Note that blinker_status set back to False in menu_right() *** )
        """
        # Has port blinker been run already?
        if not g_vars["blinker_status"]:
            # ignore any more key presses as this could cause us issues
            g_vars["disable_keys"] = True
            g_vars["blinker_process"] = subprocess.Popen(BLINKER_FILE)
            g_vars["blinker_status"] = True

            # re-enable front panel keys
            g_vars["disable_keys"] = False

        else:
            self.alert_obj.display_alert_info(
                g_vars, "Blinking eth0. Watch port LEDs on the switch.", title="Success"
            )
            g_vars["blinker_status"] = True

    def stop_blinker(self, g_vars):
        if g_vars["blinker_status"]:
            g_vars["blinker_process"].kill()
            g_vars["blinker_status"] = False
        else:
            self.alert_obj.display_alert_info(
                g_vars, "Port Blinker stopped.", title="Success"
            )

    def show_reachability(self, g_vars):
        """
        Check if default gateway, internet and DNS are reachable and working
        """

        title = "Reachability"
        reachability_info: list = []

        if not g_vars["result_cache"]:
            self.paged_table_obj.display_list_as_paged_table(
                g_vars, reachability_info, title=title
            )
            self.alert_obj.display_popup_alert(g_vars, "Checking...")

        try:
            g_vars["disable_keys"] = True

            reachability_output = subprocess.check_output([REACHABILITY_FILE]).decode()
            reachability_info = reachability_output.split("\n")

            if len(reachability_info) == 0:
                reachability_info.append("Not available.")

            # final check no-one pressed a button before we render page
            if g_vars["display_state"] == "menu":
                return

            self.paged_table_obj.display_list_as_paged_table(
                g_vars, reachability_info, title=title
            )

        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            error = ["Error: ", output]
            self.simple_table_obj.display_simple_table(g_vars, error, title=title)

        finally:
            g_vars["result_cache"] = True
            g_vars["disable_keys"] = False

    def show_ssid_passphrase(self, g_vars):
        """
        Show SSID, passphrase and QR code if available
        """

        ssid = None
        passphrase = None

        if g_vars["result_cache"]:
            return

        cmd = (
            "grep -E '^ssid|^wpa_passphrase' /etc/hostapd/hostapd.conf | cut -d '=' -f2"
        )

        try:
            data = []
            ssid, passphrase = (
                subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL)
                .decode()
                .strip()
                .split("\n")
            )
            data.append(ssid.center(21, " "))
            data.append(passphrase.center(21, " "))
        except Exception:
            self.alert_obj.display_alert_error(g_vars, "No SSID/Passphrase is set")
            return

        # final check no-one pressed a button before we render page
        if g_vars["display_state"] == "menu":
            return

        self.simple_table_obj.display_simple_table(
            g_vars, data, title="SSID/Passphrase"
        )

        # Display QR code
        env_utils = EnvUtils()

        # Get path to QR code png (it will be generated if not present)
        qrcode_path = env_utils.get_wifi_qrcode(ssid, passphrase)
        if qrcode_path is not None:
            self.display_obj.stamp_qrcode(
                g_vars, qrcode_path, center_vertically=False, y=52
            )

        g_vars["result_cache"] = True

    def show_usb(self, g_vars):
        """
        Return a list of non-Linux USB interfaces found with the lsusb command
        """

        lsusb = r"/usr/bin/lsusb | /bin/grep -v Linux | /usr/bin/cut -d\  -f7-"
        lsusb_info = []

        try:
            lsusb_output = subprocess.check_output(lsusb, shell=True).decode()
            lsusb_info = lsusb_output.split("\n")
        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            # error_descr = "Issue getting usb info using lsusb command"
            interfaces = ["Err: lsusb error", str(output)]
            self.simple_table_obj.display_simple_table(g_vars, interfaces)
            return

        interfaces = []

        for result in lsusb_info:
            interfaces.append(result)

        if len(interfaces) == 0:
            interfaces.append("No devices detected")

        # final check no-one pressed a button before we render page
        if g_vars["display_state"] == "menu":
            return

        self.simple_table_obj.display_simple_table(
            g_vars, interfaces, title="USB Devices"
        )

        return

    def show_ufw(self, g_vars):
        """
        Return a list ufw ports
        """
        ufw_file = UFW_FILE

        # check ufw is available
        if not os.path.isfile(ufw_file):
            self.alert_obj.display_alert_error(g_vars, "UFW is not installed.")

            g_vars["display_state"] = "page"
            return

        # Use cached ufw data if we have it (cleared when leaving the page)
        ufw_info = g_vars.get("ufw_info")

        if ufw_info is None:
            try:
                ufw_output = subprocess.check_output(
                    ["sudo", ufw_file, "status"]
                ).decode()
                ufw_info = ufw_output.split("\n")
                g_vars["ufw_info"] = ufw_info  # cache results
            except Exception as ex:
                error_descr = "Issue getting ufw info using ufw command"
                interfaces = ["Err: ufw error", error_descr, str(ex)]
                self.simple_table_obj.display_simple_table(g_vars, interfaces)
                return

        if not ufw_info:
            ufw_info = ["No UFW info detected"]

        port_entries = []

        # Add in status line
        port_entries.append(ufw_info[0])

        port_entries.append("Ports:")

        # lose top 4 & last 2 lines of output
        ufw_info = ufw_info[4:-2]

        for result in ufw_info:
            # tidy/compress the output
            result = result.strip()
            result_list = result.split()

            final_result = " ".join(result_list)

            port_entries.append(final_result)

        if len(port_entries) == 0:
            port_entries.append("No UF info detected")

        # final check no-one pressed a button before we render page
        if g_vars["display_state"] == "menu":
            return

        self.paged_table_obj.display_list_as_paged_table(
            g_vars, port_entries, title="UFW Ports"
        )

        return
