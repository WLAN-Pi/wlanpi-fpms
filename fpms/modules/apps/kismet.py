import subprocess

from fpms.modules.pages.alert import Alert
from fpms.modules.pages.display import Display
from fpms.modules.pages.pagedtable import PagedTable


class Kismet:
    def __init__(self, g_vars):
        self.display_obj = Display(g_vars)

        self.paged_table_obj = PagedTable(g_vars)

        self.alert_obj = Alert(g_vars)

    def kismet_status(self):
        """
        Checks the status of the Kismet service.
        Returns true if Kismet is running, false otherwise.
        """
        try:
            cmd = ["/bin/systemctl", "is-active", "--quiet", "kismet"]
            subprocess.run(cmd).check_returncode()
        except Exception:
            return False

        return True

    def kismet_ctl(self, g_vars, action):
        if g_vars["result_cache"]:
            g_vars["disable_keys"] = False
            return True

        g_vars["drawing_in_progress"] = True

        g_vars["disable_keys"] = True

        if action == "start":
            if self.kismet_status():
                self.alert_obj.display_alert_info(
                    g_vars, "Kismet already started.", title="Success"
                )
            else:
                self.alert_obj.display_popup_alert(g_vars, "Starting...")
                try:
                    cmd = ["/bin/systemctl", "start", "kismet"]
                    subprocess.run(cmd, timeout=10)
                    self.alert_obj.display_alert_info(
                        g_vars, "Kismet started.", title="Success"
                    )
                except subprocess.CalledProcessError:
                    self.alert_obj.display_alert_error(g_vars, "Start failed.")
                except subprocess.TimeoutExpired:
                    self.alert_obj.display_alert_error(g_vars, "Process timed out.")
        elif action == "stop":
            if not self.kismet_status():
                self.alert_obj.display_alert_error(g_vars, "Kismet already stopped.")
            else:
                self.alert_obj.display_popup_alert(g_vars, "Stopping...")
                try:
                    cmd = ["/bin/systemctl", "stop", "kismet"]
                    subprocess.run(cmd)
                    if self.kismet_status():
                        self.alert_obj.display_alert_error(g_vars, "Stop failed.")
                    else:
                        self.alert_obj.display_alert_info(
                            g_vars, "Kismet stopped.", title="Success"
                        )
                except subprocess.CalledProcessError:
                    self.alert_obj.display_alert_error(g_vars, "Stop failed.")

        g_vars["result_cache"] = True
        g_vars["display_state"] = "page"
        g_vars["drawing_in_progress"] = False
        return

    def kismet_start(self, g_vars):
        self.kismet_ctl(g_vars, "start")
        return

    def kismet_stop(self, g_vars):
        self.kismet_ctl(g_vars, "stop")
        return
