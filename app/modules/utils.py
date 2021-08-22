import subprocess
import os.path
import os
import time

from modules.pages.simpletable import * 
from modules.pages.pagedtable import *
from modules.constants import (
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

    def show_speedtest(self, g_vars):
        '''
        Run speedtest.net speed test and format output to fit the OLED screen
        ( *** Note that speedtest_status set back to False in menu_right() *** )
        '''
        # Has speedtest been run already?
        if g_vars['speedtest_status'] == False:

            # ignore any more key presses as this could cause us issues
            g_vars['disable_keys'] = True

            self.simple_table_obj.display_dialog_msg(g_vars, 'Running Speedtest. Please wait.', back_button_req=0)

            speedtest_info = []
            speedtest_cmd = "speedtest | egrep -w \"Testing from|Download|Upload\" | sed -r 's/Testing from.*?\(/My IP: /g; s/\)\.\.\.//g; s/Download/D/g; s/Upload/U/g; s/bit\/s/bps/g'"

            try:
                speedtest_output = subprocess.check_output(speedtest_cmd, shell=True).decode().strip()
                speedtest_info = speedtest_output.split('\n')
            except subprocess.CalledProcessError as exc:
                output = exc.output.decode()
                error = ["Err: Speedtest error", output]
                self.simple_table_obj.display_simple_table(g_vars, error, back_button_req=1)
                # re-enable front panel keys
                g_vars['disable_keys'] = False
                return

            if len(speedtest_info) == 0:
                speedtest_info.append("No output sorry")

            # chop down output to fit up to 2 lines on display
            g_vars['speedtest_result_text'] = []

            for n in speedtest_info:
                g_vars['speedtest_result_text'].append(n[0:20])
                if len(n) > 20:
                    g_vars['speedtest_result_text'].append(n[20:40])

            g_vars['speedtest_status'] = True

        # re-enable front panel keys
        g_vars['disable_keys'] = False

        self.simple_table_obj.display_simple_table(g_vars, g_vars['speedtest_result_text'], back_button_req=1, title='--Speedtest--')

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
            self.simple_table_obj.display_dialog_msg(g_vars, 'Blinking eth0. Watch port LEDs on the switch.', back_button_req=1)
            g_vars['blinker_status'] = True

    def stop_blinker(self, g_vars):
        g_vars['blinker_process'].kill()
        g_vars['blinker_status'] = False
        self.simple_table_obj.display_dialog_msg(g_vars, 'Port Blinker stopped.', back_button_req=1)

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
            self.simple_table_obj.display_simple_table(g_vars, error, back_button_req=1)
            return

        if len(reachability_info) == 0:
            reachability_info.append("No output sorry")

        # chop down output to fit up to 2 lines on display
        choppedoutput = []

        for n in reachability_info:
            choppedoutput.append(n[0:20])
            if len(n) > 20:
                choppedoutput.append(n[20:40])

        # final check no-one pressed a button before we render page
        if g_vars['display_state'] == 'menu':
            return

        self.paged_table_obj.display_list_as_paged_table(g_vars, choppedoutput, back_button_req=1, title='--Reachability')
    
    def show_wpa_passphrase(self, g_vars):
        '''
        Show WPA passphrase
        '''
        swpc = "sudo grep 'wpa_passphrase' /etc/hostapd.conf | cut -d '=' -f2"

        try:
            wpa_passphrase = []
            wpa_passphrase_output = subprocess.check_output(swpc, shell=True).decode()
            wpa_passphrase.append(wpa_passphrase_output)

        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            swperror = ["Err: WPA passphrase", output]
            self.simple_table_obj.display_simple_table(g_vars, swperror, back_button_req=1)
            return

        # final check no-one pressed a button before we render page
        if g_vars['display_state'] == 'menu':
            return

        # chop down output to fit up to 2 lines on display
        choppedoutput = []

        for n in wpa_passphrase:
            choppedoutput.append(n[0:20])
            if len(n) > 20:
                choppedoutput.append(n[20:40])

        self.simple_table_obj.display_simple_table(g_vars, choppedoutput, back_button_req=1, title='--WPA passphrase--')
    
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
            self.simple_table_obj.display_simple_table(g_vars, interfaces, back_button_req=1)
            return

        interfaces = []

        for result in lsusb_info:

            # chop down the string to fit the display
            result = result[0:19]

            interfaces.append(result)

        if len(interfaces) == 0:
            interfaces.append("No devices detected")

        # final check no-one pressed a button before we render page
        if g_vars['display_state'] == 'menu':
            return

        self.simple_table_obj.display_simple_table(g_vars, interfaces, back_button_req=1, title='--USB Interfaces--')

        return


    def show_ufw(self, g_vars):
        '''
        Return a list ufw ports
        '''
        ufw_file = UFW_FILE

        ufw_info = []

        # check ufw is available
        if not os.path.isfile(ufw_file):

            self.simple_table_obj. display_dialog_msg(g_vars, 'UFW not installed', back_button_req=1)

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
                self.simple_table_obj.display_simple_table(g_vars, interfaces, back_button_req=1)
                return
        else:
            # we must have cached results from last time
            ufw_info = g_vars['result_cache']

        port_entries = []

        # Add in status line
        port_entries.append(ufw_info[0])

        # lose top 4 & last 2 lines of output
        ufw_info = ufw_info[4:-2]

        for result in ufw_info:

            # tidy/compress the output
            result = result.strip()
            result_list = result.split()

            final_result = ' '.join(result_list)

            port_entries.append(final_result)

        if len(port_entries) == 0:
            port_entries.append("No ufw info detected")

        # final check no-one pressed a button before we render page
        if g_vars['display_state'] == 'menu':
            return

        self.paged_table_obj.display_list_as_paged_table(g_vars, port_entries, back_button_req=1, title='--UFW Summary--')

        return
