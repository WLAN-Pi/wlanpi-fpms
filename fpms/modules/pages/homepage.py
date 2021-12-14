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
from fpms.modules.constants import *

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
            return '15 Mbps/30 Mbps'

    def if_address(self, if_name):
        '''
        Returns the IP address for the given interface
        '''
        ip_addr = "No IP address"

        cmd = "ip addr show {}  2>/dev/null | grep -Po \'inet \K[\d.]+\' | head -n 1".format(if_name)
        try:
            output = subprocess.check_output(cmd, shell=True).decode().strip()
            if len(output) > 0:
                ip_addr = output
        except Exception as ex:
            pass

        return ip_addr

    def if_link_status(self, if_name):
        '''
        Returns the link status for the given interface
        '''

        status = None
        try:
            eth_info = subprocess.check_output(
                '{} {} 2>/dev/null'.format(ETHTOOL_FILE, if_name), shell=True).decode()
            speed_re = re.findall(r'Speed\: (.*\/s)', eth_info, re.MULTILINE)
            duplex_re = re.findall(r'Duplex\: (.*)', eth_info, re.MULTILINE)
            link_re = re.findall(r'Link detected\: (.*)',
                                eth_info, re.MULTILINE)

            if (speed_re is None) or (duplex_re is None) or (link_re is None):
                # Our pattern matching failed...silently fail....we must set up logging at some stage
                pass
            elif (link_re[0] == "no"):
                # Ethernet link is down, report msg instead of speed & duplex
                status = "Link down"
            else:
                # Report the speed & duplex messages from ethtool
                status = "{} {}".format(speed_re[0], duplex_re[0])

        except Exception as ex:
            # Something went wrong...show nothing
            pass

        return status

    def home_page(self, g_vars, menu):
        if PLATFORM == "pro":
            self.home_page_pro(g_vars, menu)
        else:
            self.home_page_legacy(g_vars, menu)

    def home_page_pro(self, g_vars, menu):
        x = 0
        y = 0
        padding = 2

        g_vars['drawing_in_progress'] = True
        g_vars['display_state'] = 'page'
        canvas = g_vars['draw']

        self.display_obj.clear_display(g_vars)

        if_name = "eth0"
        mode_name = "Classic Mode"
        mode = self.default_mode

        if g_vars['current_mode'] == "wconsole":
            if_name = "wlan0"
            mode_name = "Wi-Fi Console"
            mode = self.wconsole_mode
        elif g_vars['current_mode'] == "hotspot":
            if_name = "wlan0"
            mode_name = "Hotspot"
            mode = self.hotspot_mode

        elif g_vars['current_mode'] == "wiperf":
            if_name = "wlan0"
            mode_name = "Wiperf"
            mode = self.wiperf_mode

        elif g_vars['current_mode'] == "server":
            if_name = "eth0"
            mode_name = "DHCP Server"
            mode = self.dhcp_server_mode

        # Display status bar
        y += self.status_bar(g_vars)
        y += padding * 2

        # Display mode
        canvas.text((x + (PAGE_WIDTH - FONTB13.getsize(mode_name)[0])/2, y + padding), mode_name.upper(), font=FONTB13, fill=THEME.text_highlighted_color.value)
        y += 14 + padding * 2

        mode(g_vars, x=x, y=y, padding=padding)

        # Display system bar
        self.system_bar(g_vars, x=0, y=PAGE_WIDTH-SYSTEM_BAR_HEIGHT-1)

        oled.drawImage(g_vars['image'])
        g_vars['drawing_in_progress'] = False

    def home_page_legacy(self, g_vars, menu):

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
            ip_addr = "No IP address"

        x = 0
        y = 0
        padding = 2

        self.display_obj.clear_display(g_vars)

        canvas = g_vars['draw']
        canvas.text((x + padding, y + 1), str(g_vars['wlanpi_ver']), font=SMART_FONT, fill=THEME.text_color.value)
        canvas.text((x + padding, y + 11), str(g_vars['hostname']), font=FONT11, fill=THEME.text_color.value)
        canvas.text((x + padding + 95, y + 20), if_name, font=SMART_FONT, fill=THEME.text_color.value)
        canvas.text((x + padding, y + 29), str(ip_addr), font=FONT14, fill=THEME.text_color.value)
        canvas.text((x + padding, y + 43), str(mode_name), font=SMART_FONT, fill=THEME.text_color.value)

        oled.drawImage(g_vars['image'])

        g_vars['drawing_in_progress'] = False
        return

    def iface_details(self, g_vars, if_name, x=0, y=0, padding=2):
        '''
        Displays the IP address and link status details for the given interface
        '''

        canvas = g_vars['draw']
        offset = 0

        addr = self.if_address(if_name)
        link_status = self.if_link_status(if_name)
        if addr != None:
            text_color = THEME.text_color.value if addr.lower() != "no ip address" else THEME.text_important_color.value
            canvas.text((x + (PAGE_WIDTH - FONTB12.getsize(addr)[0])/2, y + padding + offset), addr, font=FONTB12, fill=text_color)
            offset += 13
        if link_status != None:
            canvas.text((x + (PAGE_WIDTH - SMART_FONT.getsize(link_status)[0])/2, y + padding + offset), link_status, font=SMART_FONT, fill=THEME.text_secondary_color.value)
            offset += 11

        return offset

    def default_mode(self, g_vars, x=0, y=0, padding=2):
        canvas = g_vars['draw']
        y += self.iface_details(g_vars, "eth0", x=x, y=y, padding=padding)
        y += 12

        # If bluetooth is on and we're paired with a device, show the PAN address
        bluetooth = Bluetooth(g_vars)
        if bluetooth.bluetooth_power() == True:
            paired_devices = bluetooth.bluetooth_paired_devices()
            if paired_devices != None:
                pan = self.if_address("pan0")
                if pan.lower() != "no ip address":
                    pan_info = f"PAN: {pan}"
                    canvas.text((x + (PAGE_WIDTH - SMART_FONT.getsize(pan_info)[0])/2, y), pan_info, font=SMART_FONT, fill=THEME.text_tertiary_color.value)
                    y += 11

        # If the eth0 interface link is down, show the USB (OTG) address
        eth_link_status = self.if_link_status("eth0")
        if eth_link_status == "Link down":
            usb = self.if_address("usb0")
            if usb.lower() != "no ip address":
                usb_info = f"USB: {usb}"
                canvas.text((x + (PAGE_WIDTH - SMART_FONT.getsize(usb_info)[0])/2, y), usb_info, font=SMART_FONT, fill=THEME.text_tertiary_color.value)
                y += 11

    def hotspot_mode(self, g_vars, x=0, y=0, padding=2):
        canvas = g_vars['draw']
        y += self.iface_details(g_vars, "wlan0", x=x, y=y, padding=padding)
        y += 12
        clients = self.wifi_client_count() + " clients"
        canvas.text((x + (PAGE_WIDTH - SMART_FONT.getsize(clients)[0])/2, y), clients, font=SMART_FONT, fill=THEME.text_tertiary_color.value)

    def wconsole_mode(self, g_vars, x=0, y=0, padding=2):
        self.iface_details(g_vars, "wlan0", x=x, y=y, padding=padding)

    def wiperf_mode(self, g_vars, x=0, y=0, padding=2):
        canvas = g_vars['draw']
        y += self.iface_details(g_vars, "wlan0", x=x, y=y, padding=padding)
        y += 12
        status = self.check_wiperf_status()
        canvas.text((x + (PAGE_WIDTH - SMART_FONT.getsize(status)[0])/2, y), status, font=SMART_FONT, fill=THEME.text_tertiary_color.value)

    def dhcp_server_mode(self, g_vars, x=0, y=0, padding=2):
        self.iface_details(g_vars, "eth0", x=x, y=y, padding=padding)

    def temperature_indicator(self, g_vars, x, y, width, height):
        '''
        Displays a system temperature indicator
        '''

        temp_high  = 80 # thermal throttling kicks in
        temp_med   = 65 # getting uncomfortable
        temp_low   = 55 # getting warmer but ok

        try:
            temp = int(open('/sys/class/thermal/thermal_zone0/temp').read())
        except:
            temp = 0

        if temp > 1000:
            temp = temp/1000

        canvas = g_vars['draw']

        if temp >= temp_high:
            temp_color = THEME.status_bar_temp_high.value
        elif temp >= temp_med:
            temp_color = THEME.status_bar_temp_med.value
        else:
            temp_color = THEME.status_bar_temp_low.value

        # draw thermometer
        canvas.ellipse((x, y + 7, x + 6, y + 13), fill=temp_color)
        canvas.rounded_rectangle((x + 2, y + 1, x + 4, y + 11), fill=THEME.status_bar_background.value, outline=temp_color, radius=1)

        # draw marks
        canvas.line((x + 6, y + 2, x + 7, y + 2), fill=temp_color)
        canvas.line((x + 6, y + 4, x + 7, y + 4), fill=temp_color)
        canvas.line((x + 6, y + 6, x + 7, y + 6), fill=temp_color)

        # fill thermometer
        if temp >= temp_high:
            canvas.rounded_rectangle((x + 2, y + 2, x + 4, y + 11), fill=temp_color, radius=1)
        elif temp >= temp_med:
            canvas.rounded_rectangle((x + 2, y + 4, x + 4, y + 11), fill=temp_color, radius=1)
        elif temp >= temp_low:
            canvas.rounded_rectangle((x + 2, y + 6, x + 4, y + 11), fill=temp_color, radius=1)

        return True

    def bluetooth_indicator(self, g_vars, x, y, width, height):
        '''
        Displays a bluetooth icon if bluetooth is on
        '''
        bluetooth = Bluetooth(g_vars)
        canvas = g_vars['draw']
        if bluetooth.bluetooth_present() and bluetooth.bluetooth_power():
            canvas.text((x, y), chr(0xf128), font=ICONS, fill=THEME.status_bar_foreground.value)
            return True

        return False

    def battery_indicator(self, g_vars, x, y, width, height):
        '''
        Displays a battery indicator that shows charge level and power status
        '''
        battery = Battery(g_vars)

        # Draw indicator
        canvas = g_vars['draw']
        bx = x + 2
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
                bx = x + 2
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

        return True

    def status_bar(self, g_vars, x=0, y=0, padding=2, width=PAGE_WIDTH, height=STATUS_BAR_HEIGHT):

        canvas = g_vars['draw']

        canvas.rectangle((x, y, width, height), fill=THEME.status_bar_background.value)
        canvas.text((x + padding + 2, y + 2), time.strftime("%H:%M"), font=FONTB11, fill=THEME.status_bar_foreground.value)

        # We position each indicator starting from the right edge of the status bar
        x = width - 24

        # Battery indicator
        if self.battery_indicator(g_vars, x, y + 2, width, height):
            x -= 10

        # Temperature indicator
        if self.temperature_indicator(g_vars, x, y + 1, width, height):
            x -= 10

        # Bluetooth indicator
        if self.bluetooth_indicator(g_vars, x, y + 1, width, height):
            x -= 10

        return height

    def system_bar(self, g_vars, x=0, y=0, padding=2, width=PAGE_WIDTH, height=SYSTEM_BAR_HEIGHT):

        canvas = g_vars['draw']

        # Draw background
        canvas.rectangle((x, y, width, y + height), fill=THEME.system_bar_background.value)

        # Draw hostname
        hostname = g_vars['hostname']
        canvas.text((x + padding, y + padding), hostname, font=SMART_FONT, fill=THEME.system_bar_foreground.value)

        # Draw version
        version = g_vars['wlanpi_ver'].split()[-1]
        size = SMART_FONT.getsize(version)
        canvas.text((width - size[0] - padding, y + padding), version, font=SMART_FONT, fill=THEME.system_bar_foreground.value)

        return height
