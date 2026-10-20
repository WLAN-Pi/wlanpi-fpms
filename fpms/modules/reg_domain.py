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

    def set_reg_domain(self, g_vars, domain):
        self.alert_obj.display_popup_alert(g_vars, "Setting domain", delay=2)

        try:
            subprocess.check_output([REG_DOMAIN_FILE, "set", domain, "--no-prompt"])
            time.sleep(1)
        except subprocess.CalledProcessError as exc:
            print(exc)
            self.alert_obj.display_alert_error(g_vars, "Failed to set domain")
            g_vars["display_state"] = "menu"
            return False

        self.alert_obj.display_popup_alert(g_vars, "Domain set", delay=2.5)
        return True
