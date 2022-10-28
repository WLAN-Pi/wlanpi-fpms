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
    
    def get_timezones_menu_format(self):
        """
        Returns a dictionary of supported Timezones as {country, [timezones]}, the timezones are filtered into country menus
        The menu names are used as the parameter for the TIME_ZONE_FILE command so show on the screen in long form : country/city
        """
        timezone_menu_list = []
        try:
            timezones_available = subprocess.getoutput(f"{TIME_ZONE_FILE} list").splitlines()
            time.sleep(1)

            # create a set of countries defined as the first part of the text split with '/'
            countries = sorted(set([c.split('/', 1)[0] for c in timezones_available])) 

            # Iterate the countries and then create array of timezones for that country
            for country in countries:
                timezone_menu_list.append({"country": country, "timezones": []})
                for timezone in filter(lambda c: c.startswith(country), timezones_available):
                    timezone_menu_list[-1]['timezones'].append(timezone.split('/', 1)[-1])

            return timezone_menu_list

        except subprocess.CalledProcessError as exc:
            return None

    def set_time_zone_from_gvars(self, g_vars):
        timezone_selected = g_vars['timezone_selected']
        self.alert_obj.display_popup_alert(g_vars, 'Setting TZ: {0}'.format(timezone_selected), delay=2)

        try:
            alert_msg = subprocess.check_output(f"{TIME_ZONE_FILE} set {timezone_selected}", shell=True).decode()
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

    # def set_time_zone_london(self, g_vars):
    #     self.alert_obj.display_popup_alert(g_vars, 'Setting time zone', delay=2)

    #     try:
    #         alert_msg = subprocess.check_output(f"{TIME_ZONE_FILE} set Europe/London", shell=True).decode()
    #         time.sleep(1)
    #     except subprocess.CalledProcessError as exc:
    #         print(exc)
    #         self.alert_obj.display_alert_error(g_vars, 'Failed to set time zone')
    #         g_vars['display_state'] = 'menu'
    #         return

    #     self.alert_obj.display_popup_alert(g_vars, 'Successfully set', delay=1)
    #     g_vars['display_state'] = 'menu'
    #     g_vars['shutdown_in_progress'] = True
    #     oled.drawImage(g_vars['reboot_image'])
    #     time.sleep(1)
    #     os.system('reboot')
    #     return

    # def set_time_zone_prague(self, g_vars):
    #     self.alert_obj.display_popup_alert(g_vars, 'Setting time zone', delay=2)

    #     try:
    #         alert_msg = subprocess.check_output(f"{TIME_ZONE_FILE} set Europe/Prague", shell=True).decode()
    #         time.sleep(1)
    #     except subprocess.CalledProcessError as exc:
    #         print(exc)
    #         self.alert_obj.display_alert_error(g_vars, 'Failed to set time zone')
    #         g_vars['display_state'] = 'menu'
    #         return

    #     self.alert_obj.display_popup_alert(g_vars, 'Successfully set', delay=1)
    #     g_vars['display_state'] = 'menu'
    #     g_vars['shutdown_in_progress'] = True
    #     oled.drawImage(g_vars['reboot_image'])
    #     time.sleep(1)
    #     os.system('reboot')
    #     return