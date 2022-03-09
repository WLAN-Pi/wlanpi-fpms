#################################################
# Create a page object that renders dispay page
#################################################
import fpms.modules.wlanpi_oled as oled
import subprocess
import re
import os.path
import time
import textfsm
import threading

from PIL import Image

from fpms.modules.pages.display import *
from fpms.modules.pages.simpletable import *
from fpms.modules.battery import *
from fpms.modules.bluetooth import *
from fpms.modules.apps.profiler import *
from fpms.modules.themes import THEME
from fpms.modules.constants import *
from fpms.modules.env_utils import EnvUtils

class HomePage(object):

    def __init__(self, g_vars):
        # load textfsm template to parse iw output
        with open(
            os.path.realpath(os.path.join(os.getcwd(), "modules/templates/iw_dev.textfsm"))
        ) as f:
            self.iw_textfsm_template = textfsm.TextFSM(f)

        # grab a screeb obj
        self.display_obj = Display(g_vars)

        # create simple table
        self.simple_table_obj = SimpleTable(g_vars)

        # create a profiler object
        self.profiler_obj = Profiler(g_vars)

        # create env utils object
        self.env_obj = EnvUtils()

        thread = threading.Thread(target=self.check_reachability, args=(g_vars,), daemon=True)
        thread.start()

    def wifi_client_count(self):
        '''
        Get a count of connected clients when in hotspot mode
        '''
        cmd = "sudo /sbin/iw dev wlan0 station dump | grep 'Station' | wc -l"

        try:
            client_count = subprocess.check_output(cmd, shell=True).decode().strip()
            return int(client_count)
        except subprocess.CalledProcessError as exc:
            return -1

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

    def check_reachability(self, g_vars):

        # Detect changes in the IP address assigned to any interface
        address_set = self.if_addresses()
        if g_vars['eth_last_known_address_set'] != address_set:
            g_vars['eth_last_known_address_set'] = address_set
            g_vars['eth_last_reachability_test'] = 0

        # Run a reachability test if enough time has passed
        last_reachability_test = g_vars['eth_last_reachability_test']
        if last_reachability_test > 0:
            g_vars['eth_last_reachability_test'] = last_reachability_test - 1
        else:
            # check reachability every 30 seconds
            g_vars['eth_last_reachability_test'] = 30

            reachability_cmd = "sudo " + REACHABILITY_FILE + " | grep -i 'browse google' | grep OK"

            try:
                subprocess.run(reachability_cmd,
                    shell=True,
                    stderr=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    check=True)
                g_vars['eth_last_reachability_result'] = True
            except subprocess.CalledProcessError as exc:
                g_vars['eth_last_reachability_result'] = False


    def if_addresses(self):
        '''
        Returns the set of IP addresses set on the device (for all interfaces)
        '''
        cmd = "ifconfig | grep -E 'inet[6]?' | awk '{ print $2 }'"
        try:
            output = subprocess.check_output(cmd, shell=True).decode().strip().split()
            return set(output)
        except:
            pass

        return {}


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
        except:
            pass

        return ip_addr

    def if_wireless(self, if_name):
        '''
        Returns True if the interface is a wireless interface, False otherwise.
        '''

        try:
            subprocess.run("iw dev {} info".format(if_name),
                shell=True,
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                check=True)
            return True
        except:
            pass

        return False

    def if_link_status(self, if_name):
        '''
        Returns the link status for the given interface
        '''

        # Check if the interface is a wireless interface, if so, we skip it
        if self.if_wireless(if_name):
            return None

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

        except:
            # Something went wrong...show nothing
            pass

        return status

    def home_page(self, g_vars, menu):
        if PLATFORM == "pro" or PLATFORM == "waveshare":
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
        mode_name = "WLAN Pi Pro"
        mode = self.classic_mode

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
        elif g_vars['current_mode'] == "bridge":
            if_name = "usb0"
            mode_name = "Bridge Mode"
            mode = self.bridge_mode

        system_bar_contents = self.env_obj.get_hostname()

        # Display status bar
        y += self.status_bar(g_vars)
        y += padding * 4

        # Display mode
        display_alternate_title = False
        title = mode_name
        if g_vars['home_page_alternate'] == True:
            if g_vars['current_mode'] == "classic":
                if self.profiler_obj.profiler_beaconing():
                    display_alternate_title = True
                    title = self.profiler_obj.profiler_beaconing_ssid()
            else:
                display_alternate_title = True

        # Truncate title if too long
        if len(title) > 21:
            title = title[0:19] + ".."

        if display_alternate_title:
            y -= 2
            canvas.text((x + (PAGE_WIDTH - FONTB10.getsize(title)[0])/2, y), title, font=FONTB10, fill=THEME.text_highlighted_color.value)
            y += 10 + padding * 2
        else:
            canvas.text((x + (PAGE_WIDTH - FONTB13.getsize(title)[0])/2, y + padding), title, font=FONTB13, fill=THEME.text_highlighted_color.value)
            y += 14 + padding * 2

        mode(g_vars, x=x, y=y, padding=padding)

        # Display system bar
        self.system_bar(g_vars, system_bar_contents, x=0, y=PAGE_WIDTH-SYSTEM_BAR_HEIGHT-1)

        # Display any overlay alerts
        if g_vars['home_page_alternate']:
            self.profiler_obj.profiler_check_new_profile(g_vars)

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
            mode_name = "Hotspot " + str(self.wifi_client_count()) + " clients"

        elif g_vars['current_mode'] == "wiperf":
            # get wlan0 IP
            if_name = "wlan0"
            mode_name = "Wiperf" + self.check_wiperf_status()

        elif g_vars['current_mode'] == "server":
            # get eth0 IP
            if_name = "eth0"
            mode_name = "DHCP Server Enabled!"
        
        elif g_vars['current_mode'] == "bridge":
            # get usb0 IP
            if_name = "usb0"
            mode_name = "Bridge Mode"

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

        hostname = self.env_obj.get_hostname()

        canvas = g_vars['draw']
        canvas.text((x + padding, y + 1), str(g_vars['wlanpi_ver']), font=SMART_FONT, fill=THEME.text_color.value)
        canvas.text((x + padding, y + 11), hostname, font=FONT11, fill=THEME.text_color.value)
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

        return offset + 8


    def iface_summary(self, g_vars, if_name, label, x=0, y=0, padding=2):
        '''
        Displays a custom label and IP address for the given interface
        '''

        canvas = g_vars['draw']
        addr = self.if_address(if_name)
        if addr.lower() != "no ip address":
            info = f"{label}: {addr}"
            canvas.text((x + (PAGE_WIDTH - SMART_FONT.getsize(info)[0])/2, y), info, font=SMART_FONT, fill=THEME.text_tertiary_color.value)
            return 11

        return 0


    def classic_mode(self, g_vars, x=0, y=0, padding=2):
        if not self.profiler_obj.profiler_beaconing():
            g_vars['home_page_alternate'] = False

        if g_vars['home_page_alternate']:
            self.profiler_qrcode(g_vars, x, y)
        else:
            canvas = g_vars['draw']
            y += self.iface_details(g_vars, "eth0", x=x, y=y, padding=padding)

            # Show the eth1 (tethered) address
            y += self.iface_summary(g_vars, "eth1", "ETH1", x=x, y=y)

            # Show the usb1 (tethered, Android) address
            y += self.iface_summary(g_vars, "usb1", "USB1", x=x, y=y)

            # Show the PAN address if bluetooth is on and we're paired with a device
            pan = self.if_address("pan0")
            if pan.lower() != "no ip address":
                bluetooth = Bluetooth(g_vars)
                if bluetooth.bluetooth_power():
                    paired_devices = bluetooth.bluetooth_paired_devices()
                    if paired_devices != None:
                        y += self.iface_summary(g_vars, "pan0", "PAN", x=x, y=y)

            # Show the USB (OTG) address
            y += self.iface_summary(g_vars, "usb0", "OTG", x=x, y=y)


    def hotspot_mode(self, g_vars, x=0, y=0, padding=2):
        if g_vars['home_page_alternate']:
            self.wifi_qrcode(g_vars, x, y)
        else:
            canvas = g_vars['draw']
            y += self.iface_details(g_vars, "wlan0", x=x, y=y, padding=padding)

            client_count = self.wifi_client_count()
            if client_count >= 0:
                clients = str(client_count) + (" client" if client_count == 1 else " clients")
                canvas.text((x + (PAGE_WIDTH - SMART_FONT.getsize(clients)[0])/2, y), clients, font=SMART_FONT, fill=THEME.text_secondary_color.value)
                y += 18

            # Show the eth0 address
            y += self.iface_summary(g_vars, "eth0", "LAN", x=x, y=y)

            # Show the USB (OTG) address
            y += self.iface_summary(g_vars, "usb0", "OTG", x=x, y=y)


    def wconsole_mode(self, g_vars, x=0, y=0, padding=2):
        if g_vars['home_page_alternate']:
            self.wifi_qrcode(g_vars, x, y)
        else:
            y += self.iface_details(g_vars, "wlan0", x=x, y=y, padding=padding)

            # Show the eth0 address
            y += self.iface_summary(g_vars, "eth0", "LAN", x=x, y=y)

            # Show the USB (OTG) address
            y += self.iface_summary(g_vars, "usb0", "OTG", x=x, y=y)
    
    def bridge_mode(self, g_vars, x=0, y=0, padding=2):
        # Show the USB (OTG) address
        y += self.iface_summary(g_vars, "usb0", "OTG", x=x, y=y)


    def wiperf_mode(self, g_vars, x=0, y=0, padding=2):
        canvas = g_vars['draw']
        y += self.iface_details(g_vars, "wlan0", x=x, y=y, padding=padding)
        y += 12
        status = self.check_wiperf_status()
        canvas.text((x + (PAGE_WIDTH - SMART_FONT.getsize(status)[0])/2, y), status, font=SMART_FONT, fill=THEME.text_tertiary_color.value)

    def dhcp_server_mode(self, g_vars, x=0, y=0, padding=2):
        if g_vars['home_page_alternate']:
            self.wifi_qrcode(g_vars, x, y)
        else:
            # Show eth0 details
            y += self.iface_details(g_vars, "eth0", x=x, y=y, padding=padding)

            # Show the USB (OTG) address
            y += self.iface_summary(g_vars, "usb0", "OTG", x=x, y=y)


    def profiler_qrcode(self, g_vars, x, y):
        '''
        Displays the profiler QR code
        '''
        # Get path to QR code png (it will be generated if not present)
        qrcode_path = self.profiler_obj.profiler_qrcode()
        if qrcode_path != None:
            self.display_obj.stamp_qrcode(g_vars, qrcode_path,
                center_vertically=False, y=y+2, draw_immediately=False)


    def wifi_qrcode(self, g_vars, x, y):
        '''
        Displays the Wi-Fi QR code
        '''
        # Get path to QR code png (it will be generated if not present)
        qrcode_path = self.env_obj.get_wifi_qrcode_for_hostapd()
        if qrcode_path != None:
            self.display_obj.stamp_qrcode(g_vars, qrcode_path,
                center_vertically=False, y=y, draw_immediately=False)


    def battery_indicator(self, g_vars, x, y, width, height):
        '''
        Displays a battery indicator that shows charge level and power status
        '''
        battery = Battery(g_vars)

        # Draw indicator
        canvas = g_vars['draw']
        bx = x + 3
        by = y + 2

        battery_indicator_width  = 16
        battery_indicator_height = 8
        canvas.rounded_rectangle((bx, by, bx + battery_indicator_width, by + battery_indicator_height), radius=1, outline=THEME.status_bar_foreground.value)

        bx = bx + battery_indicator_width
        by = by + 3
        canvas.rectangle((bx , by, bx+1, by + 2), fill=THEME.status_bar_foreground.value)

        if battery.battery_present():

            status = battery.battery_status()
            charge = battery.battery_charge()

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


    def temperature_indicator(self, g_vars, x, y, width, height):
        '''
        Displays a system temperature indicator
        '''

        temp_high  = 80 # thermal throttling kicks in
        temp_med   = 74 # getting uncomfortable
        temp_low   = 68 # getting warmer but ok

        try:
            temp = int(open('/sys/class/thermal/thermal_zone0/temp').read())
        except:
            temp = 0

        if temp > 1000:
            temp = temp/1000

        # do not draw if temperature is ok
        if temp < temp_low:
            return False

        canvas = g_vars['draw']

        if temp >= temp_high:
            temp_color = THEME.status_bar_temp_high.value
        elif temp >= temp_med:
            temp_color = THEME.status_bar_temp_med.value
        elif temp >= temp_low:
            temp_color = THEME.status_bar_temp_low.value
        else:
            temp_color = THEME.status_bar_foreground.value

        x = x + (width - 6) / 2

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


    def wifi_indicator(self, g_vars, interfaces, if_name, x, y, width, height):
        '''
        Displays a wifi indicator for the given wifi interface
        '''
        canvas = g_vars['draw']
        status_up = False
        monitor_mode = False
        active = False

        for iface in interfaces:
            if iface[1] == if_name:

                # phy index
                phy = iface[0]

                # check if the interface is UP
                try:
                    subprocess.run(f"{IFCONFIG_FILE} {if_name} | grep UP",
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=True)
                    status_up = True
                except Exception as e:
                    pass

                for other_iface in interfaces:
                    if phy == other_iface[0]:
                        if other_iface[2] == "monitor":
                            monitor_mode = True

                            # check if it's being used for capturing with tcpdump or dumpcap
                            try:
                                subprocess.run(f"ps aux 2>&1 | grep -v grep | grep -E 'tcpdump|dumpcap' | grep {other_iface[1]}",
                                    shell=True,
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL,
                                    check=True)
                                active = True
                            except Exception as e:
                                pass

                if monitor_mode and not active:
                    # check if the interface is being used for capturing with Profiler
                    if self.profiler_obj.profiler_interface() == if_name:
                        if self.profiler_obj.profiler_beaconing():
                            active = True

                fill_color = THEME.status_bar_foreground.value

                if active:
                    fill_color = THEME.status_bar_wifi_active.value

                # draw wifi icon
                if status_up or monitor_mode:
                    canvas.pieslice((x, y + 3, x + height, y + height + 3), 225, 315, fill=fill_color)
                    if monitor_mode:
                        # draw the monitor mode 'eye'
                        canvas.ellipse((x + height/2 - 3, y + height/2 - 2, x + height/2 + 3, y + height/2), fill=THEME.status_bar_background.value)
                        canvas.ellipse((x + height/2 - 1, y + height/2 - 2, x + height/2 + 1, y + height/2), fill=fill_color)
                else:
                    canvas.pieslice((x, y + 3, x + height, y + height + 3), 225, 315, outline=fill_color)

                canvas.text((x + width/2 + 3, y + height - 8), if_name[-1], font=TINY_FONT, fill=fill_color)

                return True

        return False


    def bluetooth_indicator(self, g_vars, x, y, width, height):
        '''
        Displays a bluetooth icon if bluetooth is on
        '''

        bluetooth = Bluetooth(g_vars)
        if bluetooth.bluetooth_power():
            bluetooth_icon = chr(0xf128)
            canvas = g_vars['draw']
            x = x + (width - ICONS.getsize(bluetooth_icon)[0])/2 + 1
            canvas.text((x, y), bluetooth_icon, font=ICONS, fill=THEME.status_bar_foreground.value)
            return True

        return False


    def reachability_indicator(self, g_vars, x, y, width, height):
        '''
        Displays a 'world' icon if we can reach the Internet via the Ethernet interface
        '''

        canvas = g_vars['draw']
        canvas.ellipse((x + 4, y + 2, x + height, y + height - 2), outline=THEME.status_bar_foreground.value)
        canvas.ellipse((x + 7, y + 2, x + height - 3, y + height - 2), outline=THEME.status_bar_foreground.value)
        canvas.line((x + 4, y + height/2, x + height, y + height/2), fill=THEME.status_bar_foreground.value)

        if g_vars['eth_last_reachability_result'] != True:
            canvas.line((x + 3, y + 1, x + height, y + height - 2), fill=THEME.status_bar_foreground.value, width=2)

        return True


    def status_bar(self, g_vars, x=0, y=0, padding=2, width=PAGE_WIDTH, height=STATUS_BAR_HEIGHT):

        canvas = g_vars['draw']

        current_time = time.strftime("%H:%M")
        current_time_width = FONTB11.getsize(current_time)[0]
        canvas.rectangle((x, y, width, height), fill=THEME.status_bar_background.value)
        canvas.text((x + padding + 2, y + 2), current_time, font=FONTB11, fill=THEME.status_bar_foreground.value)

        # We position each indicator starting from the right edge of the status bar
        x = width - 24
        fixed_indicator_width = 16

        # Battery indicator
        if self.battery_indicator(g_vars, x, y + 2, 24, height):
            x -= fixed_indicator_width

        y += 1
        height -= 2

        # Temperature indicator
        if x > current_time_width:
            if self.temperature_indicator(g_vars, x, y, fixed_indicator_width, height):
                x -= fixed_indicator_width

        # WiFi Indicators
        try:
            '''
            Get the list of wireless interfaces from iw and parse it as:
                [["phy_index", "interface_name", "type"], ...]
            e.g.
                [["0", "wlan0", "managed"], ["0", "wlan0mon", "monitor"], ["1", "wlan1", "managed"]]
            '''
            iw_dev_output = subprocess.check_output(f"{IW_FILE} dev 2>&1", shell=True).decode().strip()
            self.iw_textfsm_template.Reset()
            interfaces = self.iw_textfsm_template.ParseText(iw_dev_output)

            # WiFi indicator (wlan1)
            if x > current_time_width:
                if self.wifi_indicator(g_vars, interfaces, "wlan1", x, y, fixed_indicator_width, height):
                    x -= fixed_indicator_width

            # WiFi indicator (wlan0)
            if x > current_time_width:
                if self.wifi_indicator(g_vars, interfaces, "wlan0", x, y, fixed_indicator_width, height):
                    x -= fixed_indicator_width

        except Exception as e:
            print(e)

        # Bluetooth indicator
        if x > current_time_width:
            if self.bluetooth_indicator(g_vars, x, y, fixed_indicator_width, height):
                x -= fixed_indicator_width

        # Reachability indicator
        if x > current_time_width:
            if self.reachability_indicator(g_vars, x, y, fixed_indicator_width, height):
                x -= fixed_indicator_width

        return height


    def system_bar(self, g_vars, contents, x=0, y=0, padding=2, width=PAGE_WIDTH, height=SYSTEM_BAR_HEIGHT):

        canvas = g_vars['draw']

        # Draw background
        canvas.rectangle((x, y, width, y + height), fill=THEME.system_bar_background.value)

        if contents != None:
            # Truncate contents if too long
            if len(contents) > 21:
                contents = contents[0:19] + ".."

            canvas.text((x + (PAGE_WIDTH - SMART_FONT.getsize(contents)[0])/2, y + padding), contents, font=SMART_FONT, fill=THEME.system_bar_foreground.value)

        return height
