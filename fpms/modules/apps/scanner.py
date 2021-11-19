import subprocess
import threading
import fpms.modules.wlanpi_oled as oled

from fpms.modules.pages.alert import Alert
from fpms.modules.pages.pagedtable import PagedTable
from fpms.modules.constants import (
    MAX_TABLE_LINES,
    IP_FILE,
    IWCONFIG_FILE,
    IW_FILE
)

IFACE="wlan0"

class Scanner(object):

    def __init__(self, g_vars):

        # create paged table
        self.paged_table_obj = PagedTable(g_vars)

        # create alert
        self.alert_obj = Alert(g_vars)

    def freq_to_channel(self, freq_mhz):
        '''
        Converts frequency (MHz) to channel number
        '''
        if freq_mhz == 2484:
            return 14
        elif freq_mhz >= 2412 and freq_mhz <= 2484:
            return int(((freq_mhz - 2412) / 5) + 1)
        elif freq_mhz >= 5160 and freq_mhz <= 5885:
            return int(((freq_mhz - 5180) / 5) + 36)
        elif freq_mhz >= 5955 and freq_mhz <= 7115:
            return int(((freq_mhz - 5955) / 5) + 1)

        return None

    def scan(self, g_vars):

        g_vars['scanner_status'] = True

        # If you need to know exactly what this command does, ask Josh, but it
        # essentially outputs the scan results as a list of
        # bssid,freq_mhz,rssi,ssid
        # sorted by rssi
        cmd = f"{IW_FILE} {IFACE} scan | grep -wv -e 'HESSID': | grep -e '^BSS ' -e 'signal:' -e 'freq:' -e 'SSID:' | sed -e 'N;s/\\n\\t/ /' | sed -e 'N;s/\\n\\t/ /' | sed 's/\\bBSS \\b//g' | sed 's/\\b dBm\\b//g' | sed 's/\\b signal\\b://g' | sed 's/ \\bfreq\\b://g' | sed 's/ \\bSSID\\b://g' | sed 's/\\.00//' | sed 's/([^)]*)//1' | sed 's/ /,/;s/ /,/;s/ /,/' | sort -t',' -k 3"

        try:
            networks = subprocess.check_output(cmd, shell=True).decode().strip().splitlines()

            results = []
            for network in networks:
                fields = network.split(',', 3)

                # BSSID
                bssid = fields[0].upper()

                # Freq
                freq = int(fields[1])
                channel = self.freq_to_channel(freq)

                # RSSI
                rssi = int(fields[2])

                # SSID
                ssid = fields[3]

                if len(ssid) == 0:
                    ssid = "Hidden Network"

                ssid = ssid[:17]

                results.append("{} {}".format("{0: <17}".format(ssid), rssi))
                results.append("{} {}".format("{0: <17}".format(bssid), "{0: >3}".format(channel)))
                results.append("---")

            g_vars['scanner_results'] = results
        except Exception as e:
            print(e)
        finally:
            g_vars['scanner_status'] = False

    def scanner_scan(self, g_vars):

        # Check if this is the first time we run
        if g_vars['result_cache'] == False:
            # Mark results as cached (but we will keep updating in the background)
            g_vars['result_cache'] = True
            g_vars['scanner_results'] = []
            g_vars['scanner_status'] = False

            self.paged_table_obj.display_list_as_paged_table(g_vars, "", title='Networks')
            self.alert_obj.display_popup_alert(g_vars, "Scanning...")

            # Configure interface
            try:
                cmd = f"{IP_FILE} link set {IFACE} down && {IWCONFIG_FILE} {IFACE} mode managed && {IP_FILE} link set {IFACE} up"
                subprocess.run(cmd, shell=True)
            except Exception as e:
                print(e)

        else:
            if g_vars['scanner_status'] == False:
                # Run a scan in the background
                thread = threading.Thread(target=self.scan, args=(g_vars,), daemon=True)
                thread.start()

        # Check and display the results
        results = g_vars['scanner_results']

        if len(results) > 0:

            # Build the table that will display the results
            table_display_max = MAX_TABLE_LINES + int(MAX_TABLE_LINES / 3)
            pages = []
            while results:
                slice = results[:table_display_max]
                pages.append(slice)
                results = results[table_display_max:]

            table_data = {
                'title': "Networks",
                'pages': pages
            }

            # Display the results
            self.paged_table_obj.display_paged_table(g_vars, table_data, justify=False)
