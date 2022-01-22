import subprocess
import os.path
import os
import time

from PIL import Image

from fpms.modules.pages.alert import *
from fpms.modules.pages.simpletable import *
from fpms.modules.pages.pagedtable import *
from fpms.modules.env_utils import EnvUtils
from fpms.modules.constants import (
    REACHABILITY_FILE,
    BLINKER_FILE,
    UFW_FILE,
)

class Utils(object):

    def __init__(self, g_vars):

        # create simple table object to show dialog & results on display
        self.simple_table_obj = SimpleTable(g_vars)

        # create paged table
        self.paged_table_obj = PagedTable(g_vars)

        # create alert
        self.alert_obj = Alert(g_vars)

    def show_speedtest(self, g_vars):
        '''
        Run speedtest.net speed test and format output to fit the OLED screen
        ( *** Note that speedtest_status set back to False in menu_right() *** )
        '''
        # Has speedtest been run already?
        if g_vars['speedtest_status'] == False:

            # ignore any more key presses as this could cause us issues
            g_vars['disable_keys'] = True
            g_vars['speedtest_result_text'] = None

            self.alert_obj.display_popup_alert(g_vars, "Running...")

            speedtest_info = []
            speedtest_cmd = "speedtest | egrep -w \"Testing from|Download|Upload\" | sed -r 's/Testing from.*?\(/My IP: /g; s/\)\.\.\.//g; s/Download/D/g; s/Upload/U/g; s/bit\/s/bps/g'"

            try:
                speedtest_output = subprocess.check_output(speedtest_cmd, shell=True).decode().strip()
                speedtest_info = speedtest_output.split('\n')
            except subprocess.CalledProcessError as exc:
                output = exc.output.decode()
                self.alert_obj.display_alert_error(g_vars, output)
                # re-enable front panel keys
                g_vars['disable_keys'] = False
                return

            if len(speedtest_info) > 1:
                g_vars['speedtest_result_text'] = speedtest_info

            g_vars['speedtest_status'] = True

        # re-enable front panel keys
        g_vars['disable_keys'] = False

        if g_vars['speedtest_result_text'] == None:
            self.alert_obj.display_alert_error(g_vars, "Failed to run speedtest.")
        else:
            self.simple_table_obj.display_simple_table(g_vars, g_vars['speedtest_result_text'], title='Speedtest')

    def show_blinker(self, g_vars):
        '''
        Run Port Blinker on eth0 and identify switch port on the far end of the Ethernet cable
        ( *** Note that blinker_status set back to False in menu_right() *** )
        '''
        # Has port blinker been run already?
        if g_vars['blinker_status'] == False:

            # ignore any more key presses as this could cause us issues
            g_vars['disable_keys'] = True
            g_vars['blinker_process'] = subprocess.Popen(BLINKER_FILE)
            g_vars['blinker_status'] = True

            # re-enable front panel keys
            g_vars['disable_keys'] = False

        else:
            self.alert_obj.display_alert_info(g_vars, "Blinking eth0. Watch port LEDs on the switch.", title="Success")
            g_vars['blinker_status'] = True

    def stop_blinker(self, g_vars):
        if g_vars['blinker_status'] == True:
            g_vars['blinker_process'].kill()
            g_vars['blinker_status'] = False
        else:
            self.alert_obj.display_alert_info(g_vars, "Port Blinker stopped.", title="Success")

    def show_reachability(self, g_vars):
        '''
        Check if default gateway, internet and DNS are reachable and working
        '''
        reachability_info = []
        reachability_cmd = "sudo " + REACHABILITY_FILE

        try:
            reachability_output = subprocess.check_output(
                reachability_cmd, shell=True).decode()
            reachability_info = reachability_output.split('\n')

        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            error = ["Err: Reachability command error", output]
            self.simple_table_obj.display_simple_table(g_vars, error)
            return

        if len(reachability_info) == 0:
            reachability_info.append("No output sorry")

        # final check no-one pressed a button before we render page
        if g_vars['display_state'] == 'menu':
            return

        self.paged_table_obj.display_list_as_paged_table(g_vars, reachability_info, title='Reachability')

    def show_ssid_passphrase(self, g_vars):
        '''
        Show SSID, passphrase and QR code if available
        '''

        ssid = None
        passphrase = None

        if g_vars['result_cache'] == True:
            return

        cmd = "grep -E '^ssid|^wpa_passphrase' /etc/hostapd/hostapd.conf | cut -d '=' -f2"

        try:
            data = [" "]
            ssid, passphrase = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip().split("\n")
            data.append(ssid.center(21, " "))
            data.append(passphrase.center(21, " "))
        except:
            self.alert_obj.display_alert_error(g_vars, "No SSID/Passphrase is set")
            return

        # final check no-one pressed a button before we render page
        if g_vars['display_state'] == 'menu':
            return

        self.simple_table_obj.display_simple_table(g_vars, data, title='SSID/Passphrase')

        # Display QR code
        env_utils = EnvUtils()

        # Get path to QR code png (it will be generated if not present)
        qrcode_path = env_utils.get_wifi_qrcode(ssid, passphrase)
        if qrcode_path != None:
            img = Image.open(qrcode_path, 'r')
            img_w, img_h = img.size
            offset = ((PAGE_WIDTH - img_w) // 2, PAGE_HEIGHT - img_h - STATUS_BAR_HEIGHT)
            g_vars['image'].paste(img, offset)
            oled.drawImage(g_vars['image'])

        g_vars['result_cache'] = True

    def show_usb(self, g_vars):
        '''
        Return a list of non-Linux USB interfaces found with the lsusb command
        '''

        lsusb = r'/usr/bin/lsusb | /bin/grep -v Linux | /usr/bin/cut -d\  -f7-'
        lsusb_info = []

        try:
            lsusb_output = subprocess.check_output(lsusb, shell=True).decode()
            lsusb_info = lsusb_output.split('\n')
        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            #error_descr = "Issue getting usb info using lsusb command"
            interfaces = ["Err: lsusb error", str(output)]
            self.simple_table_obj.display_simple_table(g_vars, interfaces)
            return

        interfaces = []

        for result in lsusb_info:
            interfaces.append(result)

        if len(interfaces) == 0:
            interfaces.append("No devices detected")

        # final check no-one pressed a button before we render page
        if g_vars['display_state'] == 'menu':
            return

        self.simple_table_obj.display_simple_table(g_vars, interfaces, title='USB Devices')

        return


    def show_ufw(self, g_vars):
        '''
        Return a list ufw ports
        '''
        ufw_file = UFW_FILE
        ufw_info = []

        # check ufw is available
        if not os.path.isfile(ufw_file):

            self.alert_obj.display_alert_error(g_vars, "UFW is not installed.")

            g_vars['display_state'] = 'page'
            return

        # If no cached ufw data from previous screen paint, run ufw status
        if g_vars['result_cache'] == False:

            try:
                ufw_output = subprocess.check_output(
                    "sudo {} status".format(ufw_file), shell=True).decode()
                ufw_info = ufw_output.split('\n')
                g_vars['result_cache'] = ufw_info  # cache results
            except Exception as ex:
                error_descr = "Issue getting ufw info using ufw command"
                interfaces = ["Err: ufw error", error_descr, str(ex)]
                self.simple_table_obj.display_simple_table(g_vars, interfaces)
                return
        else:
            # we must have cached results from last time
            ufw_info = g_vars['result_cache']

        port_entries = []

        # Add in status line
        port_entries.append(ufw_info[0])

        port_entries.append("Ports:")

        # lose top 4 & last 2 lines of output
        ufw_info = ufw_info[4:-2]

        for result in ufw_info:

            # tidy/compress the output
            result = result.strip()
            result_list = result.split()

            final_result = ' '.join(result_list)

            port_entries.append(final_result)

        if len(port_entries) == 0:
            port_entries.append("No UF info detected")

        # final check no-one pressed a button before we render page
        if g_vars['display_state'] == 'menu':
            return

        self.paged_table_obj.display_list_as_paged_table(g_vars, port_entries, title='UFW Ports')

        return
