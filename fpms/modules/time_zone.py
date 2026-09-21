import subprocess
import time

import tzupdate

from fpms.modules.constants import TIME_ZONE_FILE
from fpms.modules.pages.alert import Alert
from fpms.modules.pages.pagedtable import PagedTable


class TimeZone:
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
        timezone_menu_list: list = []
        try:
            timezones_available = subprocess.getoutput(
                f"{TIME_ZONE_FILE} list"
            ).splitlines()
            time.sleep(1)

            # create a set of countries defined as the first part of the text split with '/'
            countries = sorted({c.split("/", 1)[0] for c in timezones_available})

            # Iterate the countries and then create array of timezones for that country
            for country in countries:
                timezone_menu_list.append({"country": country, "timezones": []})
                for timezone in filter(
                    lambda c: c.startswith(country), timezones_available
                ):
                    timezone_menu_list[-1]["timezones"].append(
                        timezone.split("/", 1)[-1]
                    )

            return timezone_menu_list

        except subprocess.CalledProcessError:
            return None

    def set_time_zone_from_gvars(self, g_vars):
        if not g_vars["result_cache"]:
            self.alert_obj.display_popup_alert(
                g_vars, "Setting timezone, please wait..."
            )
            timezone_selected = g_vars["timezone_selected"]

            try:
                subprocess.check_output(
                    f"{TIME_ZONE_FILE} set {timezone_selected}", shell=True
                ).decode()
                self.alert_obj.display_alert_info(
                    g_vars, timezone_selected, title="Success"
                )
            except subprocess.CalledProcessError as exc:
                print(exc)
                self.alert_obj.display_alert_error(
                    g_vars, "Failed to set timezone.", title="Error"
                )
                return

            time.tzset()
            g_vars["result_cache"] = True

        return

    def set_time_zone_auto(self, g_vars):
        if not g_vars["result_cache"]:
            self.alert_obj.display_popup_alert(
                g_vars, "Setting timezone, please wait..."
            )

            try:
                timezone = tzupdate.get_timezone("")
                subprocess.check_output(
                    f"{TIME_ZONE_FILE} set {timezone}", shell=True
                ).decode()
                self.alert_obj.display_alert_info(g_vars, timezone, title="Success")
            except Exception:
                self.alert_obj.display_alert_error(
                    g_vars, "Failed to set timezone.", title="Error"
                )

            time.tzset()
            g_vars["result_cache"] = True
