import json
import os.path
import re
import subprocess
import time

from fpms.modules.env_utils import EnvUtils
from fpms.modules.pages.alert import Alert
from fpms.modules.pages.display import Display
from fpms.modules.pages.pagedtable import PagedTable

PROFILER_INFO_FILE = "/run/wlanpi-profiler.info.json"
PROFILER_CONFIG_FILE = "/etc/wlanpi-profiler/config.ini"


def read_profiler_passphrase():
    """
    Returns the passphrase the Profiler is using, or None if it cannot be
    determined. The front panel QR code must carry the real passphrase: in AP
    mode a mismatch means the client never completes authentication, so no
    association request is ever captured.
    """
    try:
        with open(PROFILER_INFO_FILE) as f:
            passphrase = json.load(f).get("passphrase")
        if passphrase:
            return passphrase
    except (OSError, ValueError, AttributeError):
        pass

    try:
        with open(PROFILER_CONFIG_FILE) as f:
            for line in f:
                match = re.match(r"^passphrase:\s*(.+)$", line.strip())
                if match:
                    return match.group(1).strip()
    except OSError:
        pass

    return None


class Profiler:
    def __init__(self, g_vars):
        self.display_obj = Display(g_vars)

        self.paged_table_obj = PagedTable(g_vars)

        self.alert_obj = Alert(g_vars)

    def profiler_ctl_file_update(self, fields_dict, filename):
        with open(filename) as f:
            lines = f.readlines()

        for key, value in fields_dict.items():
            for count, line in enumerate(lines):
                if line.startswith(key):
                    lines[count] = f"{key}: {value}\n"

        with open(filename, "w") as f:
            f.writelines(lines)

    def profiler_beaconing(self):
        """
        Checks the presence of /var/run/wlanpi-profiler.ssid to determine whether
        or not the Profiler is beaconing
        """
        ssid_file = "/var/run/wlanpi-profiler.ssid"
        if os.path.exists(ssid_file):
            return True
        else:
            return False

    def profiler_beaconing_ssid(self):
        """
        Returns the SSID currently in used by the Profiler
        """
        ssid_file = "/var/run/wlanpi-profiler.ssid"
        if os.path.exists(ssid_file):
            with open(ssid_file) as f:
                return f.read()
        return None

    def profiler_last_profile_date(self):
        """
        Returns the date when the last profile was done
        """
        last_profile_file = "/var/run/wlanpi-profiler.last_profile"
        if os.path.exists(last_profile_file):
            return os.path.getmtime(last_profile_file)
        return None

    def profiler_last_profile(self):
        """
        Returns the MAC address of the client from the last profile
        """
        last_profile_file = "/var/run/wlanpi-profiler.last_profile"
        if os.path.exists(last_profile_file):
            with open(last_profile_file) as f:
                return f.read()
        return None

    def profiler_interface(self):
        """
        Returns the name of the interface configured to be used with the Profiler
        """
        config_file = "/etc/wlanpi-profiler/config.ini"
        with open(config_file) as f:
            lines = f.readlines()
            for line in lines:
                if not line.strip().startswith("#"):
                    if m := re.search(r"^interface:\s+(.+)", line):
                        return m.group(1)
        return None

    def profiler_qrcode(self):
        """
        Generates and returns the path to a WiFi QR code to be used for profiling
        """
        ssid = self.profiler_beaconing_ssid()
        passphrase = read_profiler_passphrase()
        if ssid is not None and passphrase:
            return EnvUtils().get_wifi_qrcode(ssid, passphrase)

        return None

    def profiler_check_new_profile(self, g_vars):
        """
        Checks if there's a new profile. Returns True if a new profiler is found
        and notifies the user by displaying a popup alert with the
        client's MAC address for 5 seconds
        """
        last_profile_date = self.profiler_last_profile_date()
        if last_profile_date != g_vars["profiler_last_profile_date"]:
            g_vars["profiler_last_profile_date"] = last_profile_date
            last_profile = self.profiler_last_profile().upper()
            if len(last_profile) == 12:
                last_profile = ":".join(
                    last_profile[i : i + 2] for i in range(0, len(last_profile), 2)
                )
            self.alert_obj.display_popup_alert(
                g_vars, f"Device Profiled\n{last_profile}", delay=5
            )
            return True

        return False

    def profiler_ctl(self, g_vars, action="status"):
        """
        Function to start/stop and get status of Profiler processes
        """
        beaconing = self.profiler_beaconing()
        if g_vars["profiler_beaconing"] != beaconing:
            g_vars["profiler_beaconing"] = beaconing
            if action == "status":
                g_vars["result_cache"] = False

        if action == "status" or action.startswith("start"):
            if beaconing:
                if self.profiler_check_new_profile(g_vars):
                    g_vars["result_cache"] = False

        if g_vars["result_cache"]:
            g_vars["disable_keys"] = False
            return True

        g_vars["drawing_in_progress"] = True

        g_vars["disable_keys"] = True

        try:
            cmd = ["systemctl", "is-enabled", "wlanpi-profiler"]
            subprocess.run(cmd).check_returncode()
        except Exception:
            self.alert_obj.display_alert_error(g_vars, "wlanpi-profiler not available.")
            g_vars["display_state"] = "page"
            g_vars["result_cache"] = True
            return True

        config_file = "/etc/wlanpi-profiler/config.ini"

        if action == "status":
            status = []

            with open(config_file) as f:
                lines = f.readlines()
                for line in lines:
                    if not line.strip().startswith("#"):
                        if m := re.search(r"^channel:\s+(.+)", line):
                            status.append(f"Channel: {m.group(1)}")

                        if m := re.search(r"^interface:\s+(.+)", line):
                            status.append(f"Interface: {m.group(1)}")

            if len(status) > 0:
                status = ["Targets:", *status]

            if beaconing:
                status.append(f"SSID: {self.profiler_beaconing_ssid()}")

            self.paged_table_obj.display_list_as_paged_table(
                g_vars,
                status,
                title="Profiler Active" if beaconing else "Profiler Inactive",
            )

            if beaconing:
                qrcode_path = self.profiler_qrcode()
                if qrcode_path is not None:
                    self.display_obj.stamp_qrcode(
                        g_vars, qrcode_path, center_vertically=False, y=56
                    )

        elif action.startswith("start"):
            print(action)

            if action == "start":
                cfg_dict = {
                    "channel": "36",
                    "ft_disabled": "False",
                    "he_disabled": "False",
                }
                self.profiler_ctl_file_update(cfg_dict, config_file)

            elif action == "start_2dot4ghz":
                cfg_dict = {
                    "channel": "11",
                    "ft_disabled": "False",
                    "he_disabled": "False",
                }
                self.profiler_ctl_file_update(cfg_dict, config_file)

            elif action == "start_5ghz_unii1":
                cfg_dict = {
                    "channel": "36",
                    "ft_disabled": "False",
                    "he_disabled": "False",
                }
                self.profiler_ctl_file_update(cfg_dict, config_file)

            elif action == "start_5ghz_unii3":
                cfg_dict = {
                    "channel": "149",
                    "ft_disabled": "False",
                    "he_disabled": "False",
                }
                self.profiler_ctl_file_update(cfg_dict, config_file)

            elif action == "start_no11r":
                cfg_dict = {
                    "channel": "36",
                    "ft_disabled": "True",
                    "he_disabled": "False",
                }
                self.profiler_ctl_file_update(cfg_dict, config_file)

            elif action == "start_no11ax":
                cfg_dict = {
                    "channel": "36",
                    "ft_disabled": "False",
                    "he_disabled": "True",
                }
                self.profiler_ctl_file_update(cfg_dict, config_file)

            else:
                print(f"Unknown profiler action: {action}")

            qrcode_offset = 50
            if self.profiler_beaconing():
                self.alert_obj.display_alert_info(
                    g_vars, "Profiler already started.", title="Success"
                )
                qrcode_offset = qrcode_offset + 4
            else:
                self.alert_obj.display_popup_alert(g_vars, "Starting...")
                try:
                    cmd = ["/bin/systemctl", "start", "wlanpi-profiler"]
                    subprocess.run(cmd, timeout=10)

                    elapsed_time: float = 0
                    max_wait = 20
                    while not self.profiler_beaconing() and elapsed_time <= max_wait:
                        time.sleep(0.5)
                        elapsed_time = elapsed_time + 0.5

                    if self.profiler_beaconing():
                        self.alert_obj.display_alert_info(
                            g_vars, "Profiler started.", title="Success"
                        )
                    else:
                        self.alert_obj.display_alert_error(g_vars, "Start failed.")

                except subprocess.CalledProcessError:
                    self.alert_obj.display_alert_error(g_vars, "Start failed.")
                except subprocess.TimeoutExpired:
                    self.alert_obj.display_alert_error(g_vars, "Process timed out.")

            qrcode_path = self.profiler_qrcode()
            if qrcode_path is not None:
                self.display_obj.stamp_qrcode(
                    g_vars, qrcode_path, center_vertically=False, y=qrcode_offset
                )

        elif action == "stop":
            if not self.profiler_beaconing():
                self.alert_obj.display_alert_error(g_vars, "Profiler already stopped.")
            else:
                self.alert_obj.display_popup_alert(g_vars, "Stopping...")
                try:
                    cmd = ["/bin/systemctl", "stop", "wlanpi-profiler"]
                    subprocess.run(cmd)

                    elapsed_time = 0
                    max_wait = 3
                    while self.profiler_beaconing() and elapsed_time <= max_wait:
                        time.sleep(0.5)
                        elapsed_time = elapsed_time + 0.5

                    if self.profiler_beaconing():
                        self.alert_obj.display_alert_error(g_vars, "Stop failed.")
                    else:
                        self.alert_obj.display_alert_info(
                            g_vars, "Profiler stopped.", title="Success"
                        )

                except subprocess.CalledProcessError:
                    self.alert_obj.display_alert_error(g_vars, "Stop failed.")

        elif action == "purge_reports":
            self.alert_obj.display_popup_alert(g_vars, "Purging reports...")

            try:
                cmd = ["/usr/sbin/profiler", "--clean", "--yes"]
                subprocess.run(cmd).check_returncode()
                self.alert_obj.display_alert_info(
                    g_vars, "Reports purged.", title="Success"
                )
            except subprocess.CalledProcessError as exc:
                alert_msg = f"Reports purge error: {exc}"
                self.alert_obj.display_alert_error(g_vars, alert_msg)
                print(alert_msg)

        elif action == "purge_files":
            self.alert_obj.display_popup_alert(g_vars, "Purging files...")

            try:
                cmd = ["/usr/sbin/profiler", "--clean", "--files", "--yes"]
                subprocess.run(cmd)
                self.alert_obj.display_alert_info(
                    g_vars, "Files purged.", title="Success"
                )
            except subprocess.CalledProcessError as exc:
                alert_msg = f"Files purge error: {exc}"
                self.alert_obj.display_alert_error(g_vars, alert_msg)
                print(alert_msg)

        g_vars["result_cache"] = True
        g_vars["display_state"] = "page"
        g_vars["drawing_in_progress"] = False
        return True

    def profiler_status(self, g_vars):
        self.profiler_ctl(g_vars, action="status")
        return

    def profiler_stop(self, g_vars):
        self.profiler_ctl(g_vars, action="stop")
        return

    def profiler_start(self, g_vars):
        self.profiler_ctl(g_vars, action="start")
        return

    def profiler_start_2dot4ghz(self, g_vars):
        self.profiler_ctl(g_vars, action="start_2dot4ghz")
        return

    def profiler_start_5ghz_unii1(self, g_vars):
        self.profiler_ctl(g_vars, action="start_5ghz_unii1")
        return

    def profiler_start_5ghz_unii3(self, g_vars):
        self.profiler_ctl(g_vars, action="start_5ghz_unii3")
        return

    def profiler_start_no11r(self, g_vars):
        self.profiler_ctl(g_vars, action="start_no11r")
        return

    def profiler_start_no11ax(self, g_vars):
        self.profiler_ctl(g_vars, action="start_no11ax")
        return

    def profiler_purge_reports(self, g_vars):
        self.profiler_ctl(g_vars, action="purge_reports")
        return

    def profiler_purge_files(self, g_vars):
        self.profiler_ctl(g_vars, action="purge_files")
        return
