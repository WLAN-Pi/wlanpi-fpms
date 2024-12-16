import time
import os
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
            self.alert_obj.display_alert_error(g_vars, 'Failed to get domain or no domain configured')
            g_vars['display_state'] = 'menu'
            return
        output[0] = 'RF Domain: ' + output[0]
        self.paged_table_obj.display_list_as_paged_table(g_vars, output, title="Show Domain")
        g_vars['display_state'] = 'page'

    def set_reg_domain_us(self, g_vars):
        self.alert_obj.display_popup_alert(g_vars, 'Setting domain', delay=2)

        try:
            alert_msg = subprocess.check_output(f"{REG_DOMAIN_FILE} set US --no-prompt", shell=True).decode()
            time.sleep(1)
        except subprocess.CalledProcessError as exc:
            print(exc)
            self.alert_obj.display_alert_error(g_vars, 'Failed to set domain')
            g_vars['display_state'] = 'menu'
            return

        self.alert_obj.display_popup_alert(g_vars, 'Successfully set', delay=1)
        g_vars['display_state'] = 'menu'
        g_vars['shutdown_in_progress'] = True
        oled.drawImage(g_vars['reboot_image'])
        time.sleep(1)
        os.system('reboot')
        return

    def set_reg_domain_ca(self, g_vars):
        self.alert_obj.display_popup_alert(g_vars, 'Setting domain', delay=2)

        try:
            alert_msg = subprocess.check_output(f"{REG_DOMAIN_FILE} set CA --no-prompt", shell=True).decode()
            time.sleep(1)
        except subprocess.CalledProcessError as exc:
            print(exc)
            self.alert_obj.display_alert_error(g_vars, 'Failed to set domain')
            g_vars['display_state'] = 'menu'
            return

        self.alert_obj.display_popup_alert(g_vars, 'Successfully set', delay=1)
        g_vars['display_state'] = 'menu'
        g_vars['shutdown_in_progress'] = True
        oled.drawImage(g_vars['reboot_image'])
        time.sleep(1)
        os.system('reboot')

    def set_reg_domain_gb(self, g_vars):
        self.alert_obj.display_popup_alert(g_vars, 'Setting domain', delay=2)

        try:
            alert_msg = subprocess.check_output(f"{REG_DOMAIN_FILE} set GB --no-prompt", shell=True).decode()
            time.sleep(1)
        except subprocess.CalledProcessError as exc:
            print(exc)
            self.alert_obj.display_alert_error(g_vars, 'Failed to set domain')
            g_vars['display_state'] = 'menu'
            return

        self.alert_obj.display_popup_alert(g_vars, 'Successfully set', delay=1)
        g_vars['display_state'] = 'menu'
        g_vars['shutdown_in_progress'] = True
        oled.drawImage(g_vars['reboot_image'])
        time.sleep(1)
        os.system('reboot')
        return

    def set_reg_domain_br(self, g_vars):
        self.alert_obj.display_popup_alert(g_vars, 'Setting domain', delay=2)

        try:
            alert_msg = subprocess.check_output(f"{REG_DOMAIN_FILE} set BR --no-prompt", shell=True).decode()
            time.sleep(1)
        except subprocess.CalledProcessError as exc:
            print(exc)
            self.alert_obj.display_alert_error(g_vars, 'Failed to set domain')
            g_vars['display_state'] = 'menu'
            return

        self.alert_obj.display_popup_alert(g_vars, 'Successfully set', delay=1)
        g_vars['display_state'] = 'menu'
        g_vars['shutdown_in_progress'] = True
        oled.drawImage(g_vars['reboot_image'])
        time.sleep(1)
        os.system('reboot')
        return

    def set_reg_domain_fr(self, g_vars):
        self.alert_obj.display_popup_alert(g_vars, 'Setting domain', delay=2)

        try:
            alert_msg = subprocess.check_output(f"{REG_DOMAIN_FILE} set FR --no-prompt", shell=True).decode()
            time.sleep(1)
        except subprocess.CalledProcessError as exc:
            print(exc)
            self.alert_obj.display_alert_error(g_vars, 'Failed to set domain')
            g_vars['display_state'] = 'menu'
            return

        self.alert_obj.display_popup_alert(g_vars, 'Successfully set', delay=1)
        g_vars['display_state'] = 'menu'
        g_vars['shutdown_in_progress'] = True
        oled.drawImage(g_vars['reboot_image'])
        time.sleep(1)
        os.system('reboot')
        return

    def set_reg_domain_cz(self, g_vars):
        self.alert_obj.display_popup_alert(g_vars, 'Setting domain', delay=2)

        try:
            alert_msg = subprocess.check_output(f"{REG_DOMAIN_FILE} set CZ --no-prompt", shell=True).decode()
            time.sleep(1)
        except subprocess.CalledProcessError as exc:
            print(exc)
            self.alert_obj.display_alert_error(g_vars, 'Failed to set domain')
            g_vars['display_state'] = 'menu'
            return

        self.alert_obj.display_popup_alert(g_vars, 'Successfully set', delay=1)
        g_vars['display_state'] = 'menu'
        g_vars['shutdown_in_progress'] = True
        oled.drawImage(g_vars['reboot_image'])
        time.sleep(1)
        os.system('reboot')
        return

    def set_reg_domain_nl(self, g_vars):
        self.alert_obj.display_popup_alert(g_vars, 'Setting domain', delay=2)

        try:
            alert_msg = subprocess.check_output(f"{REG_DOMAIN_FILE} set NL --no-prompt", shell=True).decode()
            time.sleep(1)
        except subprocess.CalledProcessError as exc:
            print(exc)
            self.alert_obj.display_alert_error(g_vars, 'Failed to set domain')
            g_vars['display_state'] = 'menu'
            return

        self.alert_obj.display_popup_alert(g_vars, 'Successfully set', delay=1)
        g_vars['display_state'] = 'menu'
        g_vars['shutdown_in_progress'] = True
        oled.drawImage(g_vars['reboot_image'])
        time.sleep(1)
        os.system('reboot')
        return

    def set_reg_domain_de(self, g_vars):
        self.alert_obj.display_popup_alert(g_vars, 'Setting domain', delay=2)

        try:
            alert_msg = subprocess.check_output(f"{REG_DOMAIN_FILE} set DE --no-prompt", shell=True).decode()
            time.sleep(1)
        except subprocess.CalledProcessError as exc:
            print(exc)
            self.alert_obj.display_alert_error(g_vars, 'Failed to set domain')
            g_vars['display_state'] = 'menu'
            return

        self.alert_obj.display_popup_alert(g_vars, 'Successfully set', delay=1)
        g_vars['display_state'] = 'menu'
        g_vars['shutdown_in_progress'] = True
        oled.drawImage(g_vars['reboot_image'])
        time.sleep(1)
        os.system('reboot')
        return

    def set_reg_domain_no(self, g_vars):
        self.alert_obj.display_popup_alert(g_vars, 'Setting domain', delay=2)

        try:
            alert_msg = subprocess.check_output(f"{REG_DOMAIN_FILE} set NO --no-prompt", shell=True).decode()
            time.sleep(1)
        except subprocess.CalledProcessError as exc:
            print(exc)
            self.alert_obj.display_alert_error(g_vars, 'Failed to set domain')
            g_vars['display_state'] = 'menu'
            return

        self.alert_obj.display_popup_alert(g_vars, 'Successfully set', delay=1)
        g_vars['display_state'] = 'menu'
        g_vars['shutdown_in_progress'] = True
        oled.drawImage(g_vars['reboot_image'])
        time.sleep(1)
        os.system('reboot')
        return
