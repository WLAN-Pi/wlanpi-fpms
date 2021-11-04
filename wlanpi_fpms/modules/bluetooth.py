import time
import os.path
import subprocess
import wlanpi_fpms.modules.wlanpi_oled as oled
import sys

from wlanpi_fpms.modules.pages.simpletable import SimpleTable
from wlanpi_fpms.modules.pages.pagedtable import PagedTable

class Bluetooth(object):

    def __init__(self, g_vars):

        # create simple table
        self.simple_table_obj = SimpleTable(g_vars)

        # create paged table
        self.paged_table_obj = PagedTable(g_vars)

    def bluetooth_name(self):
        try:
            cmd = "bt-adapter -i | grep Name | awk '{ print $2 }'"
            name = subprocess.check_output(cmd, shell=True).decode().strip()
            return name
        except subprocess.CalledProcessError as exc:
            return None

    def bluetooth_alias(self):
        try:
            cmd = "bt-adapter -i | grep Alias | awk '{ print $2 }'"
            alias = subprocess.check_output(cmd, shell=True).decode().strip()
            return alias
        except subprocess.CalledProcessError as exc:
            return None

    def bluetooth_address(self):
        try:
            cmd = "bt-adapter -i | grep Address | awk '{ print $2 }'"
            address = subprocess.check_output(cmd, shell=True).decode().strip()
            return address
        except subprocess.CalledProcessError as exc:
            return None

    def bluetooth_power(self):
        try:
            cmd = "bt-adapter -i | grep Powered | awk '{ print $2 }'"
            power = subprocess.check_output(cmd, shell=True).decode().strip()
            if power == "1":
                return True
            else:
                return False
        except subprocess.CalledProcessError as exc:
            return False

    def bluetooth_set_power(self, power):
        bluetooth_is_on = self.bluetooth_power()

        try:
            if power:
                if bluetooth_is_on:
                    return True
                cmd = "bt-adapter --set Powered 1 && echo 1 > /etc/wlanpi-bluetooth/state"
            else:
                if not bluetooth_is_on:
                    return True
                cmd = "bt-adapter --set Powered 0 && echo 0 > /etc/wlanpi-bluetooth/state"
            subprocess.run(cmd, shell=True)
            return True
        except subprocess.CalledProcessError as exc:
            return False

    def bluetooth_status(self, g_vars):
        status = []

        status.append("Name: "  + self.bluetooth_name())
        status.append("Alias: " + self.bluetooth_alias())
        status.append("Addr: "  + self.bluetooth_address().replace(":", ""))

        if self.bluetooth_power():
            status.append("Power: On")
        else:
            status.append("Power: Off")

        self.paged_table_obj.display_list_as_paged_table(g_vars, status, title="--Bluetooth Status--")

    def bluetooth_on(self, g_vars):
        if self.bluetooth_set_power(True):
            alias = self.bluetooth_alias()
            try:
                cmd = "systemctl start bt-timedpair"
                subprocess.run(cmd, shell=True)
                dialog_msg = "Discoverable as \"" + alias + "\""
            except subprocess.CalledProcessError as exc:
                dialog_msg = "Failed to pair bluetooth."
        else:
            dialog_msg = "Failed to turn on bluetooth."

        self.simple_table_obj. display_dialog_msg(g_vars, dialog_msg)
        g_vars['display_state'] = 'page'

    def bluetooth_off(self, g_vars):
        if self.bluetooth_set_power(False):
            dialog_msg = "Bluetooth is off."
        else:
            dialog_msg = "Failed to turn off bluetooth."

        self.simple_table_obj. display_dialog_msg(g_vars, dialog_msg)
        g_vars['display_state'] = 'page'