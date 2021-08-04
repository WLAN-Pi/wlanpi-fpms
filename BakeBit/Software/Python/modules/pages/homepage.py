#################################################
# Create a page object that renders dispay page
#################################################
import bakebit_128_64_oled as oled
import subprocess
import re
import os.path

from modules.pages.display import *
from modules.nav.navigation import *
from modules.pages.simpletable import *
from modules.constants import (
    SMART_FONT,
    FONT11,
    FONT14,
    ETHTOOL_FILE,
)

class HomePage(object):

    def __init__(self, g_vars):

        # grab a screeb obj
        self.display_obj = Display(g_vars)

        # grab a navigation obj
        self.nav_button_obj = NavButton(g_vars, 255, SMART_FONT)

        # create simple table
        self.simple_table_obj = SimpleTable(g_vars)
    
    def wifi_client_count(self):
        '''
        Get a count of connected clients when in hotspot mode
        ''' 
        wccc = "sudo /sbin/iw dev wlan0 station dump | grep 'Station' | wc -l"

        try:
            client_count = subprocess.check_output(wccc, shell=True).decode()

        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            #error_descr = "Issue getting number of  Wi-Fi clients"
            wccerror = ["Err: Wi-Fi client count", str(output)]
            self.simple_table_obj.display_simple_table(g_vars, wccerror, back_button_req=1)
            return

        return client_count.strip()
    
    def check_wiperf_status(self):
        '''
        Read the wiperf status file for visual status indication
        when in iperf mode
        '''

        status_file = '/tmp/wiperf_status.txt'
        if os.path.exists(status_file):
            try:
                statusf = open(status_file, 'r')
                msg = statusf.readline()
            except:
                # not much we can do, fail silently
                return ''

            # return extracted line
            return " ({})".format(msg)
        else:
            return ''

    def home_page(self, g_vars, menu):

        ethtool_file = ETHTOOL_FILE

        g_vars['drawing_in_progress'] = True
        g_vars['display_state'] = 'page'

        if g_vars['current_mode'] == "wconsole":
            # get wlan0 IP
            if_name = "wlan0"
            mode_name = "Wi-Fi Console"

        elif g_vars['current_mode'] == "hotspot":
            # get wlan0 IP
            if_name = "wlan0"
            mode_name = "Hotspot " + self.wifi_client_count() + " clients"

        elif g_vars['current_mode'] == "wiperf":
            # get wlan0 IP
            if_name = "wlan0"
            mode_name = "Wiperf" + self.check_wiperf_status()

        elif g_vars['current_mode'] == "server":
            # get eth0 IP
            if_name = "eth0"
            mode_name = "DHCP Server Enabled!"

        else:
            # get eth0 IP
            if_name = "eth0"
            mode_name = ""

            # get Ethernet port info (...for Jerry)
            try:
                eth_info = subprocess.check_output(
                    '{} eth0 2>/dev/null'.format(ethtool_file), shell=True).decode()
                speed_re = re.findall(r'Speed\: (.*\/s)', eth_info, re.MULTILINE)
                duplex_re = re.findall(r'Duplex\: (.*)', eth_info, re.MULTILINE)
                link_re = re.findall(r'Link detected\: (.*)',
                                    eth_info, re.MULTILINE)

                if (speed_re is None) or (duplex_re is None) or (link_re is None):
                    # Our pattern matching failed...silently fail....we must set up logging at some stage
                    mode_name = ""
                elif (link_re[0] == "no"):
                    # Ethernet link is down, report msg instead of speed & duplex
                    mode_name = "Link down"
                else:
                    # Report the speed & duplex messages from ethtool
                    mode_name = "{} {}".format(speed_re[0], duplex_re[0])

            except Exception as ex:
                # Something went wrong...show nothing
                mode_name = ""

            # If eth0 is down, lets show the usb0 IP address
            # in case anyone uses OTG conection & is confused
            if mode_name == "Link down":
                if_name = "usb0"
                mode_name = ""

        ip_addr_cmd = "ip addr show {}  2>/dev/null | grep -Po \'inet \K[\d.]+\' | head -n 1".format(if_name)

        try:
            ip_addr = subprocess.check_output(ip_addr_cmd, shell=True).decode()
        except Exception as ex:
            ip_addr = "No IP Addr"
        

        self.display_obj.clear_display(g_vars)
        g_vars['draw'].text((0, 1), str(g_vars['wlanpi_ver']), font=SMART_FONT, fill=255)
        g_vars['draw'].text((0, 11), str(g_vars['hostname']), font=FONT11, fill=255)
        g_vars['draw'].text((95, 20), if_name, font=SMART_FONT, fill=255)
        g_vars['draw'].text((0, 29), str(ip_addr), font=FONT14, fill=255)
        g_vars['draw'].text((0, 43), str(mode_name), font=SMART_FONT, fill=255)

        # if we're using a symbol key map, over-ride the menu button with the down symbol
        key_map_name = g_vars.get('key_map')
        key_map_type = g_vars['key_mappings'][key_map_name]['type']

        self.nav_button_obj.back(function='menu')
        oled.drawImage(g_vars['image'])

        g_vars['drawing_in_progress'] = False
        return
