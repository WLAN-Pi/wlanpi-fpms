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

    def profiler_running(self):
        try:
            # this cmd fails if process not active
            cmd = "systemctl is-active --quiet wlanpi-profiler"
            subprocess.check_output(cmd, shell=True)
            return True
        except subprocess.CalledProcessError as exc:
            return False

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
        cmd = "grep -E '^ssid' /etc/wlanpi-profiler/config.ini | cut -d ':' -f2"

        try:
            ssid = subprocess.check_output(cmd, shell=True).decode().strip()
            env_utils = EnvUtils()
            return env_utils.get_wifi_qrcode(ssid, "12345678")
        except:
            pass

        return None

    def profiler_ctl(self, g_vars, action="status"):
        """
        Function to start/stop and get status of Profiler processes
        """
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
            return

        config_file = "/etc/wlanpi-profiler/config.ini"

        # get profiler process status
        # (no check for cached result as need to re-evaluate
        # on each 1 sec main loop cycle)
        if action == "status":

            status = []
            active = self.profiler_running()

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

                        # SSID
                        try:
                            ssid = re.search("^ssid:\s+(.+)", line).group(1)
                            status.append("SSID: {}".format(ssid))
                        except AttributeError:
                            pass

                        # Interface
                        try:
                            interface = re.search("^interface:\s+(.+)", line).group(1)
                            status.append("Interface: {}".format(interface))
                        except AttributeError:
                            pass

            self.paged_table_obj.display_list_as_paged_table(
                g_vars, status, title="Profiler Active" if active else "Profiler Inactive"
            )

            if active:
                # Stamp QR code to facilitate profiling
                qrcode_path = self.profiler_qrcode()
                if qrcode_path != None:
                    self.display_obj.stamp_qrcode(g_vars, qrcode_path,
                        center_vertically=False, y=56)

            g_vars["display_state"] = "page"
            g_vars["result_cache"] = True
            return True

        if action.startswith("start"):

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
            if self.profiler_running():
                self.alert_obj.display_alert_info(
                    g_vars, "Profiler already started.", title="Success"
                )
                qrcode_offset = qrcode_offset + 4
            else:
                self.alert_obj.display_popup_alert(g_vars, "Starting...")
                try:
                    cmd = "/bin/systemctl start wlanpi-profiler"
                    subprocess.run(cmd, shell=True, timeout=2)
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

            if not self.profiler_running():
                self.alert_obj.display_alert_error(
                    g_vars, "Profiler is already stopped."
                )
            else:
                self.alert_obj.display_popup_alert(g_vars, "Stopping...")
                try:
                    cmd = "/bin/systemctl stop wlanpi-profiler"
                    subprocess.run(cmd, shell=True)
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
