import os
import subprocess
import threading
import signal
from typing import List
from datetime import datetime, timedelta
from os import kill

import textfsm

import fpms.modules.wlanpi_oled as oled
from fpms.modules.constants import IP_FILE, IW_FILE, IWCONFIG_FILE, MAX_TABLE_LINES
from fpms.modules.pages.alert import Alert
from fpms.modules.pages.pagedtable import PagedTable

IFACE = "wlan0"

class Scanner(object):
    def __init__(self, g_vars):
        # load textfsm template to parse iw output
        with open(
            os.path.realpath(os.path.join(os.getcwd(), "modules/templates/iw_scan.textfsm"))
        ) as f:
            self.iw_textfsm_template = textfsm.TextFSM(f)

        # create paged table
        self.paged_table_obj = PagedTable(g_vars)

        # create alert
        self.alert_obj = Alert(g_vars)

    def freq_to_channel(self, freq_mhz):
        """
        Converts frequency (MHz) to channel number
        """
        if freq_mhz == 2484:
            return 14
        elif freq_mhz >= 2412 and freq_mhz <= 2484:
            return int(((freq_mhz - 2412) / 5) + 1)
        elif freq_mhz >= 5160 and freq_mhz <= 5885:
            return int(((freq_mhz - 5180) / 5) + 36)
        elif freq_mhz >= 5955 and freq_mhz <= 7115:
            return int(((freq_mhz - 5955) / 5) + 1)

        return None

    def parse(self, iw_scan_output: str) -> List:
        """
        Returns a string containing a list of wireless networks

        Fields:
            [["bssid","frequency","rssi","ssid"]]

        Example:
            [["aa:bb:cc:00:11:22", "2412", "-69", "Outlaw"]]
            ...
        """
        self.iw_textfsm_template.Reset()
        return self.iw_textfsm_template.ParseText(iw_scan_output)

    def scan(self, g_vars, include_hidden, write_file):

        g_vars["scanner_status"] = True

        cmd = f"{IW_FILE} {IFACE} scan"

        try:
            scan_output = subprocess.check_output(cmd, shell=True).decode().strip()
            networks = self.parse(scan_output)

            # Sort results by RSSI
            networks.sort(key = lambda x: x[2])

            results = []
            for network in networks:
                # BSSID
                bssid = network[0].upper()

                # Freq
                freq = int(network[1])
                channel = self.freq_to_channel(freq)

                # RSSI
                rssi = int(network[2])

                # LAST SEEN
                lastseen = network[3]

                # SSID
                ssid = network[4]

                if len(ssid) == 0:
                    if not include_hidden:
                        continue
                    ssid = "Hidden Network"

                if write_file != True:
                    ssid = ssid[:17]

                    results.append("{} {}".format("{0: <17}".format(ssid), rssi))
                    results.append(
                        "{} {}".format("{0: <17}".format(bssid), "{0: >3}".format(channel))
                    )
                    results.append("---")
                else:
                    datetime_string = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")
                    time_now_value = datetime.now()
                    time_measure_value = time_now_value - timedelta(milliseconds=int(lastseen))
                    time_string = time_measure_value.strftime("%H:%M:%S")
                    results.append("\"{}\", \"{}\", \"{}\", \"{}\", \"{}\"\n".format(ssid, bssid, rssi, channel, time_string))
            g_vars["scanner_results"] = results
        except Exception as e:
            print(e)
        finally:
            g_vars["scanner_status"] = False

    def scanner_scan(self, g_vars, include_hidden=True, write_file=False):
        # Check if this is the first time we run
        if g_vars["result_cache"] == False:

            # Check if an instance of scandump is already running (saving to PCAP).
            # If running, terminate it, then start the scanner with the given options.
            if self.scanner_active(g_vars):
                self.scanner_terminate(g_vars)

            # Mark results as cached (but we will keep updating in the background)
            g_vars["result_cache"] = True
            g_vars["scanner_results"] = []
            g_vars["scanner_status"] = False

            self.paged_table_obj.display_list_as_paged_table(
                g_vars, "", title="Networks"
            )
            self.alert_obj.display_popup_alert(g_vars, "Scanning...")

            if write_file:
                # create a timestamped save location in case that option is chosen
                scandir = self.scanner_output_dir()
                timestr = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")
                save_file = scandir + "/scan_" + timestr + ".csv"
                g_vars["scan_file"] = save_file
                with open(save_file, "a+") as f:
                    f.writelines("SSID, BSS, RSSI, Channel, Time\n")

            # Configure interface
            try:
                cmd = f"{IP_FILE} link set {IFACE} down && {IWCONFIG_FILE} {IFACE} mode managed && {IP_FILE} link set {IFACE} up"
                subprocess.run(cmd, shell=True)
            except Exception as e:
                print(e)

        else:
            if g_vars["scanner_status"] == False:
                # Run a scan in the background
                thread = threading.Thread(target=self.scan, args=(g_vars,include_hidden, write_file), daemon=True)
                thread.start()

        # Check and display the results
        results = g_vars["scanner_results"]

        if len(results) > 0:
            # Build the table that will display the results
            table_display_max = MAX_TABLE_LINES + int(MAX_TABLE_LINES / 3)
            pages = []
            while results:
                if write_file == True:
                    save_file = g_vars["scan_file"]
                    if len(save_file) > 0:
                        # write to scan file
                        with open(save_file, "a+") as f:
                            f.writelines(results)
                slice = results[:table_display_max]
                pages.append(slice)
                results = results[table_display_max:]

            table_data = {"title": "Networks", "pages": pages}

            # Display the results
            self.paged_table_obj.display_paged_table(g_vars, table_data, justify=False)


    def scanner_scan_nohidden(self, g_vars):
        self.scanner_scan(g_vars, include_hidden=False, write_file=False)


    def scanner_scan_tofile_csv(self, g_vars):
        self.scanner_scan(g_vars, include_hidden=True, write_file=True)


    def scanner_scan_tofile_pcap_start(self, g_vars):
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

        if self.scanner_active(g_vars):
            self.alert_obj.display_alert_info(
                g_vars, "Scanner already started.", title="Success"
            )
        else:
            self.alert_obj.display_popup_alert(g_vars, "Starting...")

            scandir = self.scanner_output_dir()
            timestr = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")
            save_file = scandir + "/scan_" + timestr + ".pcap"

            try:
                p = subprocess.Popen(["/usr/bin/scandump", IFACE, save_file])
                g_vars["scanner_scandump_pid"] = p.pid;
                self.alert_obj.display_alert_info(
                    g_vars, "Scanner started.", title="Success"
                )
            except:
                self.alert_obj.display_alert_error(g_vars, "Start failed.")

        # signal that result is cached (stops re-painting screen)
        g_vars["result_cache"] = True
        g_vars["display_state"] = "page"
        g_vars["drawing_in_progress"] = False
        return


    def scanner_scan_tofile_pcap_stop(self, g_vars):
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

        if not self.scanner_active(g_vars):
            self.alert_obj.display_alert_info(
                g_vars, "Scanner already stopped.", title="Success"
            )
        else:
            self.alert_obj.display_popup_alert(g_vars, "Stopping...")
            self.scanner_terminate(g_vars)
            self.alert_obj.display_alert_info(
                g_vars, "Scanner stopped.", title="Success"
            )

        # signal that result is cached (stops re-painting screen)
        g_vars["result_cache"] = True
        g_vars["display_state"] = "page"
        g_vars["drawing_in_progress"] = False
        return


    def scanner_active(self, g_vars):
        '''
        Checks if the scandump process started by this object
        is still running in the background.
        '''
        if "scanner_scandump_pid" in g_vars:
            try:
                subprocess.check_output("/usr/bin/ps -p {}".format(g_vars["scanner_scandump_pid"]), shell=True)
                return True
            except subprocess.CalledProcessError:
                return False

        return False


    def scanner_terminate(self, g_vars):
        '''
        Terminate the scandump instance started by this object.
        '''
        if "scanner_scandump_pid" in g_vars:
            pid = g_vars["scanner_scandump_pid"]
            kill(pid, signal.SIGTERM)
            del g_vars["scanner_scandump_pid"]


    def scanner_output_dir(self):
        scandir = "/home/wlanpi/scanfiles"
        if not os.path.exists(scandir):
            os.makedirs(scandir)
        return scandir
