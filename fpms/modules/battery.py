import time
import os.path
import subprocess
import fpms.modules.wlanpi_oled as oled
import sys

from fpms.modules.pages.simpletable import SimpleTable
from fpms.modules.pages.pagedtable import PagedTable
from fpms.modules.pages.alert import Alert
from fpms.modules.constants import (
    BATTERY_STATUS_FILE
)

class Battery(object):

    def __init__(self, g_vars):

        # create paged table
        self.paged_table_obj = PagedTable(g_vars)

        # create alert
        self.alert_obj = Alert(g_vars)

        # load battery status info
        self.info = { "POWER_SUPPLY_PRESENT" : "0" }
        try:
            with open(BATTERY_STATUS_FILE) as f:
                self.info = dict([line.rstrip().split("=") for line in f])
        except FileNotFoundError:
            pass

    def battery_present(self):
        present = self.info["POWER_SUPPLY_PRESENT"]
        if present == "1":
            return True
        else:
            return False

    def battery_status(self):
        if self.battery_present():
            return self.info["POWER_SUPPLY_STATUS"].lower()

    def battery_charge(self):
        charge = 0
        voltage_max = 4100000
        voltage_min = 3300000

        if self.battery_present():
            voltage_now = int(self.info["POWER_SUPPLY_VOLTAGE_NOW"])
            if voltage_now >= voltage_max:
                charge = 100
            elif voltage_now <= voltage_min:
                charge = 0
            else:
                charge = ((voltage_now - voltage_min) * 100) / (voltage_max - voltage_min)

        return charge

    def battery_voltage(self):
        voltage = 0

        if self.battery_present():
            voltage = int(self.info["POWER_SUPPLY_VOLTAGE_NOW"])

        return voltage

    def battery_cycle_count(self):
        count = 0

        if self.battery_present():
            count = int(self.info["POWER_SUPPLY_CYCLE_COUNT"])

        return count

    def show_battery(self, g_vars):
        status = []

        if not self.battery_present():
            self.alert_obj.display_alert_error(g_vars, "Battery not found.")
            g_vars['display_state'] = 'page'
            return

        status.append(f"Status: {self.battery_status().capitalize()}")
        status.append(f"Charge: {int(self.battery_charge())}%")
        status.append(f"Voltage: {round(self.battery_voltage() / 1000000, 2)}V")
        status.append(f"Cycle Count: {self.battery_cycle_count()}")

        self.paged_table_obj.display_list_as_paged_table(g_vars, status, title="Battery")
        g_vars['display_state'] = 'page'
