#################################################
# Create a page object that renders dispay page
#################################################
import fpms.modules.wlanpi_oled as oled
import subprocess
import re
import os.path
import time

from fpms.modules.pages.display import *
from fpms.modules.pages.simpletable import *
from fpms.modules.battery import *
from fpms.modules.bluetooth import *
from fpms.modules.themes import THEME
from fpms.modules.constants import (
    PLATFORM,
    STATUS_BAR_HEIGHT,
    SMART_FONT,
    FONT11,
    FONT14,
    ICONS,
    ETHTOOL_FILE
)

class HomePage(object):

    def __init__(self, g_vars):

        # grab a screeb obj
        self.display_obj = Display(g_vars)

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
            self.simple_table_obj.display_simple_table(g_vars, wccerror)
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

        x = 0
        y = 0
        padding = 2

        self.display_obj.clear_display(g_vars)

        if PLATFORM == "pro":
            y += self.status_bar(g_vars)

        canvas = g_vars['draw']
        canvas.text((x + padding, y + 1), str(g_vars['wlanpi_ver']), font=SMART_FONT, fill=THEME.text_foreground.value)
        canvas.text((x + padding, y + 11), str(g_vars['hostname']), font=FONT11, fill=THEME.text_foreground.value)
        canvas.text((x + padding + 95, y + 20), if_name, font=SMART_FONT, fill=THEME.text_foreground.value)
        canvas.text((x + padding, y + 29), str(ip_addr), font=FONT14, fill=THEME.text_foreground.value)
        canvas.text((x + padding, y + 43), str(mode_name), font=SMART_FONT, fill=THEME.text_foreground.value)

        oled.drawImage(g_vars['image'])

        g_vars['drawing_in_progress'] = False
        return

    def status_bar(self, g_vars, x=0, y=0, padding=2, width=PAGE_WIDTH, height=STATUS_BAR_HEIGHT):

        canvas = g_vars['draw']

        canvas.rectangle((x, y, width, height), fill=THEME.status_bar_background.value)
        y += 2
        canvas.text((x + padding + 2, y), time.strftime("%I:%M %p"), font=SMART_FONT, fill=THEME.status_bar_foreground.value)

        # Battery indicator
        self.battery_indicator(g_vars, x, y, width, height)

        # Bluetooth indicator
        self.bluetooth_indicator(g_vars, x, y, width, height)

        return height

    def bluetooth_indicator(self, g_vars, x, y, width, height):
        bluetooth = Bluetooth(g_vars)
        canvas = g_vars['draw']
        if bluetooth.bluetooth_present() and bluetooth.bluetooth_power():
            canvas.text((width - 30, y + 1), chr(0xf128), font=ICONS, fill=THEME.status_bar_foreground.value)

    def battery_indicator(self, g_vars, x, y, width, height):
        battery = Battery(g_vars)
        offset  = 20

        # Draw indicator
        canvas = g_vars['draw']
        bx = width - offset
        by = y + 2
        status = battery.battery_status()
        charge = battery.battery_charge()

        battery_indicator_width  = 16
        battery_indicator_height = 8
        canvas.rounded_rectangle((bx, by, bx + battery_indicator_width, by + battery_indicator_height), radius=1, outline=THEME.status_bar_foreground.value)

        bx = bx + battery_indicator_width
        by = by + 3
        canvas.rectangle((bx , by, bx+1, by + 2), fill=THEME.status_bar_foreground.value)

        if battery.battery_present():

            # Draw current charge level
            if charge > 0:
                bx = width - offset
                by = y + 2
                fill_color = THEME.status_bar_foreground.value

                if status == "charging":
                    fill_color = THEME.status_bar_battery_full.value
                elif charge <= 25:
                    fill_color = THEME.status_bar_battery_low.value
                elif charge >= 100:
                    if status == "not charging":
                        fill_color = THEME.status_bar_battery_full.value

                canvas.rectangle((bx+2, by+2, bx + ((battery_indicator_width - 2) * charge / 100), by + battery_indicator_height-2), fill=fill_color)

            # Draw charging indicator (aka lighting bolt)
            if status == "charging":
                xy = [
                (bx + battery_indicator_width/2 + 1, by - 2),
                (bx + battery_indicator_width/2 - 4, by + battery_indicator_height/2 + 1),
                (bx + battery_indicator_width/2 - 1, by + battery_indicator_height/2 + 1),
                (bx + battery_indicator_width/2 - 1, by + battery_indicator_height + 2),
                (bx + battery_indicator_width/2 + 4, by + battery_indicator_height/2 - 1),
                (bx + battery_indicator_width/2 + 1, by + battery_indicator_height/2 - 1)
                ]
                canvas.polygon(xy, fill=THEME.status_bar_foreground.value, outline=THEME.status_bar_background.value)
