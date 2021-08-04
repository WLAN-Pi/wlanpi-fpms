import time
import os.path
import subprocess
import bakebit_128_64_oled as oled

from modules.pages.simpletable import SimpleTable
from modules.constants import (
    WCONSOLE_SWITCHER_FILE,
    HOTSPOT_SWITCHER_FILE,
    WIPERF_SWITCHER_FILE,
    SERVER_SWITCHER_FILE,
)

class Mode(object):

    def __init__(self, g_vars):
       
        # create simple table
        self.simple_table_obj = SimpleTable(g_vars)

    def switcher(self, g_vars, resource_title, resource_switcher_file, mode_name):
        '''
        Function to perform generic set of operations to switch wlanpi mode
        '''

        reboot_image = g_vars['reboot_image']

        # check resource is available
        if not os.path.isfile(resource_switcher_file):

            self.simple_table_obj. display_dialog_msg(g_vars, '{} not available'.format(resource_title), back_button_req=1)
            g_vars['display_state'] = 'page'
            return

        # Resource switcher was detected, so assume it's installed
        back_button_req = 0

        if g_vars['current_mode'] == "classic":
            # if in classic mode, switch to the resource
            dialog_msg = 'Switching to {} mode (rebooting...)'.format(resource_title)
            switch = "on"
        elif g_vars['current_mode'] == mode_name:
            dialog_msg = 'Switching to Classic mode (rebooting...)'
            switch = "off"
        else:
            dialog_msg('Unknown mode: {}'.format(g_vars['current_mode']), back_button_req=1)
            g_vars['display_state'] = 'page'
            return False

        # Flip the mode
        self.simple_table_obj. display_dialog_msg(g_vars, dialog_msg, back_button_req)
        g_vars['shutdown_in_progress'] = True
        time.sleep(2)

        oled.drawImage(g_vars['reboot_image'])
        g_vars['screen_cleared'] = True

        try:
            dialog_msg = subprocess.check_output("{} {}".format(resource_switcher_file, switch), shell=True).decode()  # reboots
            time.sleep(1)
        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            dialog_msg = mode_name

        # We only get to this point if the switch has failed for some reason
        # (Note that the switcher script reboots the WLANPi)
        g_vars['shutdown_in_progress'] = False
        g_vars['screen_cleared'] = False
        self.simple_table_obj. display_dialog_msg(g_vars, "Switch failed: {}".format(dialog_msg), back_button_req=0)
        g_vars['display_state'] = 'menu'

        # allow 5 secs to view failure msg
        time.sleep(3)
        # move back up to menu branch
        g_vars['current_menu_location'].pop()

        return False

    def wconsole_switcher(self, g_vars):

        wconsole_switcher_file = WCONSOLE_SWITCHER_FILE

        resource_title = "Wi-Fi Console"
        mode_name = "wconsole"
        resource_switcher_file = wconsole_switcher_file

        # switch
        self.switcher(g_vars, resource_title, resource_switcher_file, mode_name)
        return True


    def hotspot_switcher(self, g_vars):

        hotspot_switcher_file = HOTSPOT_SWITCHER_FILE

        resource_title = "Hotspot"
        mode_name = "hotspot"
        resource_switcher_file = hotspot_switcher_file

        self.switcher(g_vars, resource_title, resource_switcher_file, mode_name)
        return True


    def wiperf_switcher(self, g_vars):

        wiperf_switcher_file = WIPERF_SWITCHER_FILE

        resource_title = "Wiperf"
        mode_name = "wiperf"
        resource_switcher_file = wiperf_switcher_file

        self.switcher(g_vars, resource_title, resource_switcher_file, mode_name)
        return True


    def server_switcher(self, g_vars):

        server_switcher_file = SERVER_SWITCHER_FILE

        resource_title = "Server"
        mode_name = "server"
        resource_switcher_file = server_switcher_file

        self.switcher(g_vars, resource_title, resource_switcher_file, mode_name)
        return True
