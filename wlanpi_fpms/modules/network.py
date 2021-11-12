import time
import os
import subprocess
import re

from wlanpi_fpms.modules.pages.alert import *
from wlanpi_fpms.modules.pages.display import *
from wlanpi_fpms.modules.pages.simpletable import *
from wlanpi_fpms.modules.pages.pagedtable import *
from wlanpi_fpms.modules.constants import (
    LLDPNEIGH_FILE,
    CDPNEIGH_FILE,
    IPCONFIG_FILE,
    PUBLICIP_CMD,
    ETHTOOL_FILE,
    IFCONFIG_FILE,
    IWCONFIG_FILE,
    IW_FILE,
)

class Network(object):

    def __init__(self, g_vars):

        # grab a screeb obj
        self.display_obj = Display(g_vars)

        # create simple table
        self.simple_table_obj = SimpleTable(g_vars)

        # create paged table
        self.paged_table_obj = PagedTable(g_vars)

        # create alert
        self.alert_obj = Alert(g_vars)

    def show_interfaces(self, g_vars):
        '''
        Return a list of network interfaces found to be up, with IP address if available
        '''

        ifconfig_file = IFCONFIG_FILE
        iw_file = IW_FILE

        try:
            ifconfig_info = subprocess.check_output(
                ifconfig_file, shell=True).decode()
        except Exception as ex:
            interfaces = ["Err: ifconfig error", str(ex)]
            self.simple_table_obj.display_simple_table(g_vars, interfaces)
            return

        # Extract interface info with a bit of regex magic
        interface_re = re.findall(
            r'^(\w+?)\: flags(.*?)RX packets', ifconfig_info, re.DOTALL | re.MULTILINE)
        if interface_re is None:
            # Something broke is our regex - report an issue
            interfaces = ["Error: match error"]
        else:
            interfaces = []
            for result in interface_re:

                # save the interface name
                interface_name = result[0]

                '''
                if re.match(r'^eth', interface_name):
                    interface_name = "e{}".format(interface_name[-1])
                elif re.match(r'^wlan', interface_name):
                    interface_name = "w{}".format(interface_name[-1])
                elif re.match(r'^usb', interface_name):
                    interface_name = "u{}".format(interface_name[-1])
                elif re.match(r'^zt', interface_name):
                    interface_name = "zt"
                '''

                # look at the rest of the interface info & extract IP if available
                interface_info = result[1]

                inet_search = re.search(
                    "inet (.+?) ", interface_info, re.MULTILINE)
                if inet_search is None:
                    ip_address = "-"

                    # do check if this is an interface in monitor mode
                    if (re.search(r"wlan\d", interface_name, re.MULTILINE)):

                        # fire up 'iw' for this interface (hmmm..is this a bit of an un-necessary ovehead?)
                        try:
                            iw_info = subprocess.check_output(
                                '{} {} info'.format(iw_file, interface_name), shell=True).decode()

                            if re.search("type monitor", iw_info, re.MULTILINE):
                                ip_address = "(Monitor)"
                        except:
                            ip_address = "unknown"
                else:
                    ip_address = inet_search.group(1)

                interfaces.append('{}: {}'.format(interface_name, ip_address))

        # final check no-one pressed a button before we render page
        if g_vars['display_state'] == 'menu':
            return

        self.paged_table_obj.display_list_as_paged_table(g_vars, interfaces, title="Interfaces")

    def channel_lookup(self, freq_mhz):
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

    def show_wlan_interfaces(self, g_vars):
        '''
        Create pages to summarise WLAN interface info
        '''

        g_wlan_interfaces_key = 'network_wlan_interfaces'

        g_vars['disable_keys'] = True
        g_vars['drawing_in_progress'] = True

        # Display cached results (if any)
        if g_vars['result_cache'] == True:
            self.paged_table_obj.display_paged_table(g_vars,
                { 'title' : "WLAN Interfaces", 'pages': g_vars[g_wlan_interfaces_key] })
            g_vars['disable_keys'] = False
            return None

        interfaces = []
        pages = []

        try:
            interfaces = subprocess.check_output(f"{IWCONFIG_FILE} 2>&1 | grep 802.11" + "| awk '{ print $1 }'", shell=True).decode().strip().split()
        except Exception as e:
            print(e)

        for interface in interfaces:
            page = []
            page.append(f"Interface: {interface}")

            # Driver
            try:
                ethtool_output = subprocess.check_output(f"{ETHTOOL_FILE} -i {interface}", shell=True).decode().strip()
                driver = re.search(".*driver:\s+(.*)", ethtool_output).group(1)
                page.append(f"Driver: {driver}")
            except Exception:
                pass

            # Addr
            try:
                ifconfig_output = subprocess.check_output(f"{IFCONFIG_FILE} {interface}", shell=True).decode().strip()
                addr = re.search(".*ether\s+([^\s]*).*", ifconfig_output).group(1).replace(":", "").upper()
                page.append(f"Addr: {addr}")
            except Exception:
                pass

            # SSID, Mode, Channel
            try:
                iwconfig_output = subprocess.check_output(f"{IWCONFIG_FILE} {interface}", shell=True).decode().strip()

                # Mode
                try:
                    mode = re.search(".*Mode:([^\s]*)\s.*", iwconfig_output).group(1)
                    page.append(f"Mode: {mode}")
                except Exception:
                    pass

                # SSID
                try:
                    ssid = re.search(".*ESSID:\"([^\"]*)\".*", iwconfig_output).group(1)
                    page.append(f"SSID: {ssid}")
                except Exception:
                    pass

                # Frequency
                try:
                    freq = int(float(re.search(".*Frequency:([^\s]*)\s.*", iwconfig_output).group(1)) * 1000)
                    channel = self.channel_lookup(freq)
                    page.append(f"Freq (MHz): {freq}")
                    page.append(f"Channel: {channel}")
                except Exception:
                    pass

            except Exception as e:
                print(e)

            pages.append(page)

        self.paged_table_obj.display_paged_table(g_vars, { 'title' : "WLAN Interfaces", 'pages': pages })

        g_vars[g_wlan_interfaces_key] = pages
        g_vars['result_cache'] = True
        g_vars['display_state'] = 'page'
        g_vars['drawing_in_progress'] = False
        g_vars['disable_keys'] = False

    def show_eth0_ipconfig(self, g_vars):
        '''
        Return IP configuration of eth0 including IP, default gateway, DNS servers
        '''
        ipconfig_file = IPCONFIG_FILE

        eth0_ipconfig_info = []

        try:
            ipconfig_output = subprocess.check_output(
                ipconfig_file, shell=True).decode()
            ipconfig_info = ipconfig_output.split('\n')

        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            #error_descr = "Issue getting ipconfig"
            ipconfigerror = ["Err: ipconfig command error", output]
            self.simple_table_obj.display_simple_table(g_vars, ipconfigerror)
            return

        if len(ipconfig_info) == 0:
            eth0_ipconfig_info.append("Nothing to display")

        for n in ipconfig_info:
            # do some cleanup
            n = n.replace("DHCP server name", "DHCP")
            n = n.replace("DHCP server address", "DHCP IP")
            eth0_ipconfig_info.append(n)

        # chop down output to fit up to 2 lines on display
        choppedoutput = []

        for n in eth0_ipconfig_info:
            choppedoutput.append(n[0:20])
            if len(n) > 20:
                choppedoutput.append(n[20:40])

        # final check no-one pressed a button before we render page
        if g_vars['display_state'] == 'menu':
            return

        self.paged_table_obj.display_list_as_paged_table(g_vars, choppedoutput, title='Eth0 IP Config')

        return

    def show_vlan(self, g_vars):
        '''
        Display untagged VLAN number on eth0
        Todo: Add tagged VLAN info
        '''
        lldpneigh_file = LLDPNEIGH_FILE
        cdpneigh_file = CDPNEIGH_FILE

        vlan_info = []

        vlan_cmd = "sudo grep -a VLAN " + lldpneigh_file + \
            " || grep -a VLAN " + cdpneigh_file

        if os.path.exists(lldpneigh_file):

            try:
                vlan_output = subprocess.check_output(
                    vlan_cmd, shell=True).decode()
                vlan_info = vlan_output.split('\n')

                if len(vlan_info) == 0:
                    vlan_info.append("No VLAN found")

                # final chop down of the string to fit the display
                for n in vlan_info:
                    n = n[0:19]

            except:
                vlan_info = ["No VLAN found"]

        # final check no-one pressed a button before we render page
        if g_vars['display_state'] == 'menu':
            return

        self.simple_table_obj.display_simple_table(g_vars, vlan_info, title='Eth0 VLAN')

    def show_lldp_neighbour(self, g_vars):
        '''
        Display LLDP neighbour on eth0
        '''
        lldpneigh_file = LLDPNEIGH_FILE

        neighbour_info = []
        neighbour_cmd = "sudo cat " + lldpneigh_file

        if os.path.exists(lldpneigh_file):

            try:
                neighbour_output = subprocess.check_output(
                    neighbour_cmd, shell=True).decode()
                neighbour_info = neighbour_output.split('\n')

            except subprocess.CalledProcessError as exc:
                output = exc.output.decode()
                #error_descr = "Issue getting LLDP neighbour"
                error = ["Err: Neighbour command error", output]
                self.simple_table_obj.display_simple_table(g_vars, error)
                return

        if len(neighbour_info) == 0:
            neighbour_info.append("No neighbour")

        # chop down output to fit up to 2 lines on display
        choppedoutput = []

        for n in neighbour_info:
            choppedoutput.append(n[0:20])
            if len(n) > 20:
                choppedoutput.append(n[20:40])
            if len(n) > 40:
                choppedoutput.append(n[40:60])
            if len(n) > 60:
                choppedoutput.append(n[60:80])
            if len(n) > 80:
                choppedoutput.append(n[80:100])

        # final check no-one pressed a button before we render page
        if g_vars['display_state'] == 'menu':
            return

        #self.simple_table_obj.display_simple_table(g_vars, choppedoutput, title='--LLDP Neighbour--')
        self.paged_table_obj.display_list_as_paged_table(g_vars, choppedoutput, title='LLDP Neighbour')


    def show_cdp_neighbour(self, g_vars):
        '''
        Display CDP neighbour on eth0
        '''
        cdpneigh_file = CDPNEIGH_FILE

        neighbour_info = []
        neighbour_cmd = "sudo cat " + cdpneigh_file

        if os.path.exists(cdpneigh_file):

            try:
                neighbour_output = subprocess.check_output(
                    neighbour_cmd, shell=True).decode()
                neighbour_info = neighbour_output.split('\n')

            except subprocess.CalledProcessError as exc:
                output = exc.output.decode()
                #error_descr = "Issue getting LLDP neighbour"
                error = ["Err: Neighbour command error", output]
                self.simple_table_obj.display_simple_table(g_vars, error)
                return

        if len(neighbour_info) == 0:
            neighbour_info.append("No neighbour")

        # chop down output to fit up to 2 lines on display
        choppedoutput = []

        for n in neighbour_info:
            choppedoutput.append(n[0:20])
            if len(n) > 20:
                choppedoutput.append(n[20:40])
            if len(n) > 40:
                choppedoutput.append(n[40:60])
            if len(n) > 60:
                choppedoutput.append(n[60:80])
            if len(n) > 80:
                choppedoutput.append(n[80:100])

        # final check no-one pressed a button before we render page
        if g_vars['display_state'] == 'menu':
            return

        #self.simple_table_obj.display_simple_table(g_vars, choppedoutput, title='--CDP Neighbour--')
        self.paged_table_obj.display_list_as_paged_table(g_vars, choppedoutput, title='CDP Neighbour')

    def show_publicip(self, g_vars):
        '''
        Shows public IP address and related details, works with any interface with internet connectivity
        '''

        publicip_info = []

        try:
            publicip_output = subprocess.check_output(
                PUBLICIP_CMD, shell=True).decode().strip()
            publicip_info = publicip_output.split('\n')
        except subprocess.CalledProcessError:
            self.alert_obj.display_alert_error(g_vars, "Failed to detect public IP address")
            return

        if len(publicip_info) == 1:
            self.alert_obj.display_alert_error(g_vars, publicip_info[0])
            return

        # chop down output to fit up to 2 lines on display
        choppedoutput = []

        for n in publicip_info:
            choppedoutput.append(n[0:20])
            if len(n) > 20:
                choppedoutput.append(n[20:40])

        # final check no-one pressed a button before we render page
        if g_vars['display_state'] == 'menu':
            return

        self.paged_table_obj.display_list_as_paged_table(g_vars, choppedoutput, title='Public IP')
