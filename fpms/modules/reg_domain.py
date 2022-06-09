import time
import os.path
import subprocess
import fpms.modules.wlanpi_oled as oled
import sys

from fpms.modules.pages.simpletable import SimpleTable
from fpms.modules.pages.pagedtable import PagedTable
from fpms.modules.pages.alert import Alert
from fpms.modules.constants import (
    REG_DOMAIN_FILE
)

class RegDomain(object):

    def __init__(self, g_vars):

        # create paged table
        self.paged_table_obj = PagedTable(g_vars)

        # create alert
        self.alert_obj = Alert(g_vars)

    def show_reg_domain(self, g_vars):
        output = []
        try:
            output = subprocess.check_output(f"{REG_DOMAIN_FILE} get", shell=True).decode().strip().split("\n")
        except subprocess.CalledProcessError as exc:
            print(exc)
            self.alert_obj.display_alert_error(g_vars, 'Failed to get domain')
            g_vars['display_state'] = 'menu'
            return
        self.paged_table_obj.display_list_as_paged_table(g_vars, output, title="Show Domain")
        g_vars['display_state'] = 'page'

    def set_reg_domain_us(self, g_vars):
        self.alert_obj.display_popup_alert(g_vars, 'Setting domain to US', delay=2)

        try:
            alert_msg = subprocess.check_output(f"{REG_DOMAIN_FILE} set US", shell=True).decode()
            time.sleep(1)
        except subprocess.CalledProcessError as exc:
            print(exc)
            self.alert_obj.display_alert_error(g_vars, 'Failed to set domain')
            g_vars['display_state'] = 'menu'
            return

        self.alert_obj.display_popup_alert(g_vars, 'Domain set successfully', delay=2)
        g_vars['display_state'] = 'menu'
        return

    def set_reg_domain_gb(self, g_vars):
        self.alert_obj.display_popup_alert(g_vars, 'Setting domain to GB', delay=2)

        try:
            alert_msg = subprocess.check_output(f"{REG_DOMAIN_FILE} set GB", shell=True).decode()
            time.sleep(1)
        except subprocess.CalledProcessError as exc:
            print(exc)
            self.alert_obj.display_alert_error(g_vars, 'Failed to set domain')
            g_vars['display_state'] = 'menu'
            return

        self.alert_obj.display_popup_alert(g_vars, 'Domain set successfully', delay=2)
        g_vars['display_state'] = 'menu'
        return
