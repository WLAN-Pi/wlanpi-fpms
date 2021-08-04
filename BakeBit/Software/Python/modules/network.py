import time
import os
import subprocess
import re

from modules.pages.display import *
from modules.nav.navigation import *
from modules.pages.simpletable import *
from modules.pages.pagedtable import *
from modules.constants import (
    LLDPNEIGH_FILE,
    CDPNEIGH_FILE,
    IPCONFIG_FILE,
    PUBLICIP_CMD,
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
            self.simple_table_obj.display_simple_table(g_vars, interfaces, back_button_req=1)
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
                if re.match(r'^eth', interface_name):
                    interface_name = "e{}".format(interface_name[-1])
                elif re.match(r'^wlan', interface_name):
                    interface_name = "w{}".format(interface_name[-1])
                elif re.match(r'^usb', interface_name):
                    interface_name = "u{}".format(interface_name[-1])
                elif re.match(r'^zt', interface_name):
                    interface_name = "zt"

                # look at the rest of the interface info & extract IP if available
                interface_info = result[1]

                inet_search = re.search(
                    "inet (.+?) ", interface_info, re.MULTILINE)
                if inet_search is None:
                    ip_address = "No IP address"

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

        self.paged_table_obj.display_list_as_paged_table(g_vars, interfaces, back_button_req=1, title="--Interfaces--")

    def channel_lookup(self, freq):

        channels = {
            '2.412': 1,
            '2.417': 2,
            '2.422': 3,
            '2.427': 4,
            '2.432': 5,
            '2.437': 6,
            '2.442': 7,
            '2.447': 8,
            '2.452': 9,
            '2.457': 10,
            '2.462': 11,
            '2.467': 12,
            '2.472': 13,
            '2.484': 14,
            '5.18':  36,
            '5.2':  40,
            '5.22':  44,
            '5.24':  48,
            '5.26':  52,
            '5.28':  56,
            '5.3':   60,
            '5.32':  64,
            '5.5':   100,
            '5.52':  104,
            '5.54':  108,
            '5.56':  112,
            '5.58':  116,
            '5.6':   120,
            '5.62':  124,
            '5.64':  128,
            '5.66':  132,
            '5.68':  136,
            '5.7':   140,
            '5.72':  144,
            '5.745': 149,
            '5.765': 153,
            '5.785': 157,
            '5.805': 161,
            '5.825': 165,
        }

        return channels.get(freq, 'unknown')
    
    def field_extractor(self, field_name, pattern, cmd_output_text):

        re_result = re.search(pattern, cmd_output_text)

        if not re_result is None:
            field_value = re_result.group(1)
            return field_value
        else:
            return None

    def show_wlan_interfaces(self, g_vars):
        '''
        Create pages to summarise WLAN interface info
        '''

        ifconfig_file = IFCONFIG_FILE
        iwconfig_file = IWCONFIG_FILE

        try:
            ifconfig_info = subprocess.check_output('{} -s'.format(ifconfig_file), shell=True).decode()
        except Exception as ex:
            interfaces = ["Err: ifconfig error", str(ex)]
            self.simple_table_obj.display_simple_table(g_vars, interfaces, back_button_req=1)
            return

        # Extract interface info
        interface_re = re.findall(
            r'^(wlan\d)  ', ifconfig_info, re.DOTALL | re.MULTILINE)
        if interface_re is None:
            interfaces = ["Error: match error"]
        else:

            interfaces = []
            for interface_name in interface_re:

                interface_info = []
                ssid = False
                freq = False
                channel = False
                mode = False

                # use iwconfig to find further info for each wlan interface
                try:
                    cmd = "{} {}".format(iwconfig_file, interface_name)
                    iwconfig_info = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True).decode()
                except subprocess.CalledProcessError:
                    iwconfig_info = "Err: iwconfig cmd failed"

                # Extract SSID
                pattern = r'ESSID\:\"(.*?)\"'
                field_name = "ssid"
                extraction = self.field_extractor(
                    field_name, pattern, iwconfig_info)
                if extraction:
                    ssid = extraction

                # Extract Frequency
                pattern = r'Frequency[\:|\=](\d+\.\d+) '
                field_name = "freq"
                extraction = self.field_extractor(
                    field_name, pattern, iwconfig_info)
                if extraction:
                    freq = extraction

                # lookup channel number from freq
                if freq:
                    channel = self.channel_lookup(str(freq))
                
                # Extract Mode
                pattern = r'Mode\:(.*?) '
                field_name = "mode"
                extraction = self.field_extractor(
                    field_name, pattern, iwconfig_info)
                if extraction:
                    mode = extraction

                # construct our page data - start with name
                interface_info.append("Interface: " + interface_name)

                # SSID
                if 'ssid':
                    interface_info.append("SSID: {}".format(ssid))
                else:
                    interface_info.append("SSID: N/A")

                # Mode
                if 'mode':
                    interface_info.append( "Mode: {}".format(mode))
                else:
                    interface_info.append("Mode: N/A")

                # Channel
                if 'channel':
                    interface_info.append("Ch: {}".format(channel))
                else:
                    interface_info.append("Ch: unknown")

                interfaces.append(interface_info)

            # if we had no WLAN interfaces, insert message
            if len(interfaces) == 0:
                interfaces.append(['No Wlan Interfaces'])

        data = {
            'title': '--WLAN I/F--',
            'pages': interfaces
        }

        # final check no-one pressed a button before we render page
        if g_vars['display_state'] == 'menu':
            return

        self.paged_table_obj.display_paged_table(g_vars, data, back_button_req=1)


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
            self.simple_table_obj.display_simple_table(g_vars, ipconfigerror, back_button_req=1)
            return

        if len(ipconfig_info) == 0:
            eth0_ipconfig_info.append("Nothing to display")

        for n in ipconfig_info:
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

        self.paged_table_obj.display_list_as_paged_table(g_vars, choppedoutput, back_button_req=1, title='--Eth0 IP Cfg--')

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

            except:
                error = ["No VLAN found"]
                self.simple_table_obj.display_simple_table(g_vars, error, back_button_req=1)
                return

        if len(vlan_info) == 0:
            vlan_info.append("No VLAN found")

        # final chop down of the string to fit the display
        for n in vlan_info:
            n = n[0:19]

        # final check no-one pressed a button before we render page
        if g_vars['display_state'] == 'menu':
            return

        self.simple_table_obj.display_simple_table(g_vars, vlan_info, back_button_req=1, title='--Eth0 VLAN--')

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
                self.simple_table_obj.display_simple_table(g_vars, error, back_button_req=1)
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

        #self.simple_table_obj.display_simple_table(g_vars, choppedoutput, back_button_req=1, title='--LLDP Neighbour--')
        self.paged_table_obj.display_list_as_paged_table(g_vars, choppedoutput, back_button_req=1, title='--LLDP N/bor--')


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
                self.simple_table_obj.display_simple_table(g_vars, error, back_button_req=1)
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

        #self.simple_table_obj.display_simple_table(g_vars, choppedoutput, back_button_req=1, title='--CDP Neighbour--')
        self.paged_table_obj.display_list_as_paged_table(g_vars, choppedoutput, back_button_req=1, title='--CDP N/bor--')

    def show_publicip(self, g_vars):
        '''
        Shows public IP address and related details, works with any interface with internet connectivity
        '''
        publicip_cmd = PUBLICIP_CMD

        publicip_info = []

        try:
            publicip_output = subprocess.check_output(
                publicip_cmd, shell=True).decode()
            publicip_info = publicip_output.split('\n')

        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            #error_descr = "Public IP Error"
            error = ["Err: Public IP", output]
            self.simple_table_obj.display_simple_table(g_vars, error, back_button_req=1)
            return

        if len(publicip_info) == 0:
            publicip_info.append("No output sorry")

        # chop down output to fit up to 2 lines on display
        choppedoutput = []

        for n in publicip_info:
            choppedoutput.append(n[0:20])
            if len(n) > 20:
                choppedoutput.append(n[20:40])

        # final check no-one pressed a button before we render page
        if g_vars['display_state'] == 'menu':
            return

        self.paged_table_obj.display_list_as_paged_table(g_vars, choppedoutput, back_button_req=1, title='  --Public IP--')
        time.sleep(0.5)
