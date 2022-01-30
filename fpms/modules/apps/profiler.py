import os.path
import re
import subprocess
import sys
import time

import fpms.modules.wlanpi_oled as oled
from fpms.modules.pages.display import Display
from fpms.modules.pages.alert import Alert
from fpms.modules.pages.pagedtable import PagedTable
from fpms.modules.env_utils import EnvUtils

class Profiler(object):
    def __init__(self, g_vars):

        # create display object
        self.display_obj = Display(g_vars)

        # create paged table
        self.paged_table_obj = PagedTable(g_vars)

        # create alert
        self.alert_obj = Alert(g_vars)

    def profiler_ctl_file_update(self, fields_dict, filename):

        # read in file to an array
        with open(filename, "r") as f:
            lines = f.readlines()

        # loop through each field in values to set in file
        for key, value in fields_dict.items():

            # step through all lines and look for a match
            for count, line in enumerate(lines):
                # replace match in file with key/value pair
                if line.startswith(key):
                    lines[count] = "{}: {}\n".format(key, value)

        # write modified file back out
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
            with open(ssid_file, "r") as f:
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
            with open(last_profile_file, "r") as f:
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
                    try:
                        return re.search("^interface:\s+(.+)", line).group(1)
                    except AttributeError:
                        pass
        return None

    def profiler_qrcode(self):
        """
        Generates and returns the path to a WiFi QR code to be used for profiling
        """
        ssid = self.profiler_beaconing_ssid()
        if ssid != None:
            return EnvUtils().get_wifi_qrcode(ssid, "12345678")

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
                # Insert ":" to improve readability
                last_profile = ":".join(last_profile[i:i+2] for i in range(0, len(last_profile), 2))
            self.alert_obj.display_popup_alert(g_vars, "Device Profiled\n{}".format(last_profile), delay=5)
            return True

        return False

    def profiler_ctl(self, g_vars, action="status"):
        """
        Function to start/stop and get status of Profiler processes
        """
        # Reset result_cache if the profiler has changed state so that we
        # can update the status screen
        beaconing = self.profiler_beaconing()
        if g_vars["profiler_beaconing"] != beaconing:
            g_vars["profiler_beaconing"] = beaconing
            if action == "status":
                g_vars["result_cache"] = False

        # Check if we need to notify about a new profile. If so, set result_cache
        # to false to repaint the screen after the alert is presented
        if action == "status" or action.startswith("start"):
            if beaconing:
                if self.profiler_check_new_profile(g_vars):
                    g_vars["result_cache"] = False

        # if we're been round this loop before,
        # results treated as cached to prevent re-evaluating
        # and re-painting
        if g_vars["result_cache"] == True:
            # re-enable keys
            g_vars["disable_keys"] = False
            return True

        g_vars["drawing_in_progress"] = True

        # disable keys while we react to the key press that got us here
        g_vars["disable_keys"] = True

        # check resource is available
        try:
            # this cmd fails if service not installed
            cmd = "systemctl is-enabled wlanpi-profiler"
            subprocess.run(cmd, shell=True).check_returncode()
        except:
            # cmd failed, so profiler service not installed
            self.alert_obj.display_alert_error(g_vars, "wlanpi-profiler not available.")
            g_vars["display_state"] = "page"
            g_vars["result_cache"] = True
            return True

        config_file = "/etc/wlanpi-profiler/config.ini"

        # get profiler process status
        # (no check for cached result as need to re-evaluate
        # on each 1 sec main loop cycle)
        if action == "status":

            status = []

            # read config
            with open(config_file) as f:
                lines = f.readlines()
                for line in lines:
                    if not line.strip().startswith("#"):
                        # Channel
                        try:
                            channel = re.search("^channel:\s+(.+)", line).group(1)
                            status.append("Channel: {}".format(channel))
                        except AttributeError:
                            pass

                        # Interface
                        try:
                            interface = re.search("^interface:\s+(.+)", line).group(1)
                            status.append("Interface: {}".format(interface))
                        except AttributeError:
                            pass

            if beaconing:
                # SSID
                status.append("SSID: {}".format(self.profiler_beaconing_ssid()))

            # Compose table
            self.paged_table_obj.display_list_as_paged_table(
                g_vars, status, title="Profiler Active" if beaconing else "Profiler Inactive"
            )

            if beaconing:
                # Stamp QR code to facilitate profiling
                qrcode_path = self.profiler_qrcode()
                if qrcode_path != None:
                    self.display_obj.stamp_qrcode(g_vars, qrcode_path,
                        center_vertically=False, y=56)

        elif action.startswith("start"):

            if action == "start":
                # set the config file to use params
                cfg_dict = {"ft_enabled": "True", "he_enabled": "True"}
                self.profiler_ctl_file_update(cfg_dict, config_file)

            elif action == "start_no11r":
                # set the config file to use params
                cfg_dict = {"ft_enabled": "False", "he_enabled": "True"}
                self.profiler_ctl_file_update(cfg_dict, config_file)

            elif action == "start_no11ax":
                # set the config file to use params
                cfg_dict = {"ft_enabled": "True", "he_enabled": "False"}
                self.profiler_ctl_file_update(cfg_dict, config_file)

            else:
                print("Unknown profiler action: {}".format(action))

            qrcode_offset = 50
            if self.profiler_beaconing():
                self.alert_obj.display_alert_info(
                    g_vars, "Profiler already started.", title="Success"
                )
                qrcode_offset = qrcode_offset + 4
            else:
                self.alert_obj.display_popup_alert(g_vars, "Starting...")
                try:
                    cmd = "/bin/systemctl start wlanpi-profiler"
                    subprocess.run(cmd, shell=True, timeout=2)

                    # We need to wait until Profiler starts beaconing so that
                    # we can show the QR code. We will wait for 15 seconds and
                    # if Profiler hasn't started beaconing, then it will just
                    # tell the user that Profiler has started.
                    elapsed_time = 0
                    max_wait = 15 # seconds
                    while not self.profiler_beaconing() and elapsed_time <= max_wait:
                        time.sleep(0.5)
                        elapsed_time = elapsed_time + 0.5

                    self.alert_obj.display_alert_info(
                        g_vars, "Profiler started.", title="Success"
                    )
                except subprocess.CalledProcessError as proc_exc:
                    self.alert_obj.display_alert_error(g_vars, "Start failed.")
                except subprocess.TimeoutExpired as timeout_exc:
                    self.alert_obj.display_alert_error(g_vars, "Process timed out.")

            # Stamp QR code to facilitate profiling
            qrcode_path = self.profiler_qrcode()
            if qrcode_path != None:
                self.display_obj.stamp_qrcode(g_vars, qrcode_path,
                    center_vertically=False, y=qrcode_offset)

        elif action == "stop":

            if not self.profiler_beaconing():
                self.alert_obj.display_alert_error(
                    g_vars, "Profiler already stopped."
                )
            else:
                self.alert_obj.display_popup_alert(g_vars, "Stopping...")
                try:
                    cmd = "/bin/systemctl stop wlanpi-profiler"
                    subprocess.run(cmd, shell=True)

                    # Wait for Profiler to stop beaconing so we can check
                    # it was successfully stopped.
                    elapsed_time = 0
                    max_wait = 3 # seconds
                    while self.profiler_beaconing() and elapsed_time <= max_wait:
                        time.sleep(0.5)
                        elapsed_time = elapsed_time + 0.5

                    if self.profiler_beaconing():
                        self.alert_obj.display_alert_error(g_vars, "Stop failed.")
                    else:
                        self.alert_obj.display_alert_info(
                            g_vars, "Profiler stopped.", title="Success"
                            )
                except subprocess.CalledProcessError as exc:
                    self.alert_obj.display_alert_error(g_vars, "Stop failed.")

        elif action == "purge_reports":
            # call profiler2 with the --clean option

            self.alert_obj.display_popup_alert(g_vars, "Purging reports...")

            try:
                cmd = "/usr/sbin/profiler --clean --yes"
                subprocess.run(cmd, shell=True).check_returncode()
                self.alert_obj.display_alert_info(
                    g_vars, "Reports purged.", title="Success"
                )
            except subprocess.CalledProcessError as exc:
                alert_msg = "Reports purge error: {}".format(exc)
                self.alert_obj.display_alert_error(g_vars, alert_msg)
                print(alert_msg)

        elif action == "purge_files":
            # call profiler2 with the --clean --files option

            self.alert_obj.display_popup_alert(g_vars, "Purging files...")

            try:
                cmd = "/usr/sbin/profiler --clean --files --yes"
                subprocess.run(cmd, shell=True)
                self.alert_obj.display_alert_info(
                    g_vars, "Files purged.", title="Success"
                )
            except subprocess.CalledProcessError as exc:
                alert_msg = "Files purge error: {}".format(exc)
                self.alert_obj.display_alert_error(g_vars, alert_msg)
                print(alert_msg)

        # signal that result is cached (stops re-painting screen)
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
