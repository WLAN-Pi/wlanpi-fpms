import time
import os
import subprocess
import fpms.modules.wlanpi_oled as oled
import sys

from fpms.modules.pages.simpletable import SimpleTable
from fpms.modules.pages.pagedtable import PagedTable
from fpms.modules.pages.alert import Alert
from fpms.modules.constants import (
    TIME_ZONE_FILE
)

class TimeZone(object):

    def __init__(self, g_vars):

        # create paged table
        self.paged_table_obj = PagedTable(g_vars)

        # create alert
        self.alert_obj = Alert(g_vars)

    def set_time_zone_london(self, g_vars):
        self.alert_obj.display_popup_alert(g_vars, 'Setting time zone', delay=2)

        try:
            alert_msg = subprocess.check_output(f"{TIME_ZONE_FILE} set Europe/London", shell=True).decode()
            time.sleep(1)
        except subprocess.CalledProcessError as exc:
            print(exc)
            self.alert_obj.display_alert_error(g_vars, 'Failed to set time zone')
            g_vars['display_state'] = 'menu'
            return

        self.alert_obj.display_popup_alert(g_vars, 'Successfully set', delay=1)
        g_vars['display_state'] = 'menu'
        g_vars['shutdown_in_progress'] = True
        oled.drawImage(g_vars['reboot_image'])
        time.sleep(1)
        os.system('reboot')
        return

    def set_time_zone_prague(self, g_vars):
        self.alert_obj.display_popup_alert(g_vars, 'Setting time zone', delay=2)

        try:
            alert_msg = subprocess.check_output(f"{TIME_ZONE_FILE} set Europe/Prague", shell=True).decode()
            time.sleep(1)
        except subprocess.CalledProcessError as exc:
            print(exc)
            self.alert_obj.display_alert_error(g_vars, 'Failed to set time zone')
            g_vars['display_state'] = 'menu'
            return

        self.alert_obj.display_popup_alert(g_vars, 'Successfully set', delay=1)
        g_vars['display_state'] = 'menu'
        g_vars['shutdown_in_progress'] = True
        oled.drawImage(g_vars['reboot_image'])
        time.sleep(1)
        os.system('reboot')
        return