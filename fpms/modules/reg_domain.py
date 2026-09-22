import subprocess
import time

from fpms.modules.constants import REG_DOMAIN_FILE
from fpms.modules.pages.alert import Alert
from fpms.modules.pages.pagedtable import PagedTable


class RegDomain:
    def __init__(self, g_vars):
        # create paged table
        self.paged_table_obj = PagedTable(g_vars)

        # create alert
        self.alert_obj = Alert(g_vars)

    def show_reg_domain(self, g_vars):
        output = []
        try:
            output = (
                subprocess.check_output([REG_DOMAIN_FILE, "get"])
                .decode()
                .strip()
                .split("\n")
            )
        except subprocess.CalledProcessError as exc:
            print(exc)
            self.alert_obj.display_alert_error(
                g_vars, "Failed to get domain or no domain configured"
            )
            g_vars["display_state"] = "menu"
            return
        output[0] = "RF Domain: " + output[0]
        self.paged_table_obj.display_list_as_paged_table(
            g_vars, output, title="Show Domain"
        )
        g_vars["display_state"] = "page"

    def set_reg_domain_us(self, g_vars):
        self.alert_obj.display_popup_alert(g_vars, "Setting domain", delay=2)

        try:
            subprocess.check_output(
                [REG_DOMAIN_FILE, "set", "US", "--no-prompt"]
            ).decode()
            time.sleep(1)
        except subprocess.CalledProcessError as exc:
            print(exc)
            self.alert_obj.display_alert_error(g_vars, "Failed to set domain")
            g_vars["display_state"] = "menu"
            return

        self.alert_obj.display_popup_alert(g_vars, "Success. Reboot req.", delay=2.5)
        g_vars["display_state"] = "menu"
        return

    def set_reg_domain_ca(self, g_vars):
        self.alert_obj.display_popup_alert(g_vars, "Setting domain", delay=2)

        try:
            subprocess.check_output(
                [REG_DOMAIN_FILE, "set", "CA", "--no-prompt"]
            ).decode()
            time.sleep(1)
        except subprocess.CalledProcessError as exc:
            print(exc)
            self.alert_obj.display_alert_error(g_vars, "Failed to set domain")
            g_vars["display_state"] = "menu"
            return

        self.alert_obj.display_popup_alert(g_vars, "Success. Reboot req.", delay=2.5)
        g_vars["display_state"] = "menu"
        return

    def set_reg_domain_gb(self, g_vars):
        self.alert_obj.display_popup_alert(g_vars, "Setting domain", delay=2)

        try:
            subprocess.check_output(
                [REG_DOMAIN_FILE, "set", "GB", "--no-prompt"]
            ).decode()
            time.sleep(1)
        except subprocess.CalledProcessError as exc:
            print(exc)
            self.alert_obj.display_alert_error(g_vars, "Failed to set domain")
            g_vars["display_state"] = "menu"
            return

        self.alert_obj.display_popup_alert(g_vars, "Success. Reboot req.", delay=2.5)
        g_vars["display_state"] = "menu"
        return

    def set_reg_domain_br(self, g_vars):
        self.alert_obj.display_popup_alert(g_vars, "Setting domain", delay=2)

        try:
            subprocess.check_output(
                [REG_DOMAIN_FILE, "set", "BR", "--no-prompt"]
            ).decode()
            time.sleep(1)
        except subprocess.CalledProcessError as exc:
            print(exc)
            self.alert_obj.display_alert_error(g_vars, "Failed to set domain")
            g_vars["display_state"] = "menu"
            return

        self.alert_obj.display_popup_alert(g_vars, "Success. Reboot req.", delay=2.5)
        g_vars["display_state"] = "menu"
        return

    def set_reg_domain_fr(self, g_vars):
        self.alert_obj.display_popup_alert(g_vars, "Setting domain", delay=2)

        try:
            subprocess.check_output(
                [REG_DOMAIN_FILE, "set", "FR", "--no-prompt"]
            ).decode()
            time.sleep(1)
        except subprocess.CalledProcessError as exc:
            print(exc)
            self.alert_obj.display_alert_error(g_vars, "Failed to set domain")
            g_vars["display_state"] = "menu"
            return

        self.alert_obj.display_popup_alert(g_vars, "Success. Reboot req.", delay=2.5)
        g_vars["display_state"] = "menu"
        return

    def set_reg_domain_cz(self, g_vars):
        self.alert_obj.display_popup_alert(g_vars, "Setting domain", delay=2)

        try:
            subprocess.check_output(
                [REG_DOMAIN_FILE, "set", "CZ", "--no-prompt"]
            ).decode()
            time.sleep(1)
        except subprocess.CalledProcessError as exc:
            print(exc)
            self.alert_obj.display_alert_error(g_vars, "Failed to set domain")
            g_vars["display_state"] = "menu"
            return

        self.alert_obj.display_popup_alert(g_vars, "Success. Reboot req.", delay=2.5)
        g_vars["display_state"] = "menu"
        return

    def set_reg_domain_nl(self, g_vars):
        self.alert_obj.display_popup_alert(g_vars, "Setting domain", delay=2)

        try:
            subprocess.check_output(
                [REG_DOMAIN_FILE, "set", "NL", "--no-prompt"]
            ).decode()
            time.sleep(1)
        except subprocess.CalledProcessError as exc:
            print(exc)
            self.alert_obj.display_alert_error(g_vars, "Failed to set domain")
            g_vars["display_state"] = "menu"
            return

        self.alert_obj.display_popup_alert(g_vars, "Success. Reboot req.", delay=2.5)
        g_vars["display_state"] = "menu"
        return

    def set_reg_domain_de(self, g_vars):
        self.alert_obj.display_popup_alert(g_vars, "Setting domain", delay=2)

        try:
            subprocess.check_output(
                [REG_DOMAIN_FILE, "set", "DE", "--no-prompt"]
            ).decode()
            time.sleep(1)
        except subprocess.CalledProcessError as exc:
            print(exc)
            self.alert_obj.display_alert_error(g_vars, "Failed to set domain")
            g_vars["display_state"] = "menu"
            return

        self.alert_obj.display_popup_alert(g_vars, "Success. Reboot req.", delay=2.5)
        g_vars["display_state"] = "menu"
        return

    def set_reg_domain_no(self, g_vars):
        self.alert_obj.display_popup_alert(g_vars, "Setting domain", delay=2)

        try:
            subprocess.check_output(
                [REG_DOMAIN_FILE, "set", "NO", "--no-prompt"]
            ).decode()
            time.sleep(1)
        except subprocess.CalledProcessError as exc:
            print(exc)
            self.alert_obj.display_alert_error(g_vars, "Failed to set domain")
            g_vars["display_state"] = "menu"
            return

        self.alert_obj.display_popup_alert(g_vars, "Success. Reboot req.", delay=2.5)
        g_vars["display_state"] = "menu"
        return
