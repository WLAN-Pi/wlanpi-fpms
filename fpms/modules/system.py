import fpms.modules.wlanpi_oled as oled
import time
import os
import subprocess
import socket
import random

from PIL import ImageFont
from fpms.modules.pages.alert import *
from fpms.modules.pages.display import *
from fpms.modules.pages.simpletable import *
from fpms.modules.pages.pagedtable import *
from fpms.modules.constants import (
    SMART_FONT,
    FONT11,
    FONT12,
    FONT13,
    FONTB14,
)

class System(object):

    def __init__(self, g_vars):

        # grab a screeb obj
        self.display_obj = Display(g_vars)

        # create simple table
        self.simple_table_obj = SimpleTable(g_vars)

        # create paged table
        self.paged_table_obj = PagedTable(g_vars)

        # create alert
        self.alert_obj = Alert(g_vars)

    def shutdown(self, g_vars):

        self.alert_obj.display_popup_alert(g_vars, "Shutting down...", delay=1)
        oled.drawImage(g_vars['shutdown_image'])
        g_vars['shutdown_in_progress'] = True

        os.system('systemctl poweroff')

        return

    def reboot(self, g_vars):
        self.alert_obj.display_popup_alert(g_vars, "Rebooting...", delay=1)
        oled.drawImage(g_vars['reboot_image'])
        g_vars['shutdown_in_progress'] = True

        os.system('systemctl reboot')

        return

    def show_summary(self, g_vars):

        '''
        Summary page - taken from original bakebit script
        '''

        # The commands here take quite a while to execute, so lock screen early
        # (normally done by page drawing function)
        g_vars['drawing_in_progress'] = True

        # figure out our IP
        IP = ''
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except:
            IP = '127.0.0.1'
        finally:
            s.close()

        ipStr = f"IP: {IP}"

        # determine CPU load
        cmd = "top -bn1 | grep load | awk '{printf \"CPU Load: %.2f\", $(NF-2)}'"
        try:
            CPU = subprocess.check_output(cmd, shell=True).decode()
        except:
            CPU = "unknown"

        # determine mem useage
        cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'"
        try:
            MemUsage = subprocess.check_output(cmd, shell=True).decode()
        except:
            MemUsage = "unknown"

        # determine disk util
        cmd = "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%dGB %s\", $3,$2,$5}'"
        try:
            Disk = subprocess.check_output(cmd, shell=True).decode()
        except:
            Disk = "unknown"

        # determine temp
        try:
            tempI = int(open('/sys/class/thermal/thermal_zone0/temp').read())
        except:
            tempI = "unknown"

        if tempI > 1000:
            tempI = tempI/1000
        tempStr = "CPU Temp: %sC" % str(round(tempI, 1))

        # determine uptime
        cmd = "uptime -p | sed -r 's/up|,//g' | sed -r 's/\s*week[s]?/w/g' | sed -r 's/\s*day[s]?/d/g' | sed -r 's/\s*hour[s]?/h/g' | sed -r 's/\s*minute[s]?/m/g'"
        try:
            uptime = subprocess.check_output(cmd, shell=True).decode().strip()
        except:
            uptime = "unknown"

        uptimeStr = f"Up: {uptime}"

        results = [
            ipStr,
            str(CPU),
            str(MemUsage),
            str(Disk),
            tempStr,
            uptimeStr
        ]

        # final check no-one pressed a button before we render page
        if g_vars['display_state'] == 'menu':
            return

        self.simple_table_obj.display_simple_table(g_vars, results, title="Summary")

        return


    def show_date(self, g_vars):
        '''
        Date page - taken from original bakebit script & modified to add TZ
        '''

        g_vars['drawing_in_progress'] = True

        # Clear display prior to painting new item
        self.display_obj.clear_display(g_vars)

        clock_font = ImageFont.truetype('fonts/DejaVuSansMono-Bold.ttf', 18)
        margin = 2

        # Draw time
        text = time.strftime("%X")
        text_size = clock_font.getsize(text)
        x = (PAGE_WIDTH - text_size[0])/2
        y = PAGE_HEIGHT/4
        g_vars['draw'].text((x, y), text, font=clock_font, fill=THEME.text_important_color.value)
        y = PAGE_HEIGHT/4 + text_size[1]

        # Draw date
        text = time.strftime("%e %b. %Y")
        text_size = FONT13.getsize(text)
        x = (PAGE_WIDTH - text_size[0])/2
        y = y + margin * 2
        g_vars['draw'].text((x, y), text, font=FONT13, fill=THEME.text_color.value)
        y = y + text_size[1] + margin

        # Draw timezone
        text = "Timezone: " + time.strftime("%Z")
        text_size = FONT11.getsize(text)
        x = (PAGE_WIDTH - text_size[0])/2
        y = y + margin * 3
        g_vars['draw'].text((x, y), text, font=FONT11, fill=THEME.text_secondary_color.value)

        oled.drawImage(g_vars['image'])

        g_vars['display_state'] = 'page'
        g_vars['drawing_in_progress'] = False

    def show_about(self, g_vars):

        if g_vars['result_cache'] == False:
            g_vars["disable_keys"] = True

            name = "WLAN Pi OS"
            version = g_vars['wlanpi_ver']
            authors = None
            authors_file = os.path.realpath(os.path.join(os.getcwd(), "AUTHORS.md"))
            if os.path.isfile(authors_file):
                with open(authors_file) as f:
                    authors = "\n".join(filter(None, [line if line.startswith('*') else "" for line in f.read().splitlines()]))

            about = []
            about.append(" ")
            about.append(name.center(20, " "))
            about.append(version.center(20, " "))
            about.append(" ")

            if authors != None:
                authors_list = []
                for author in authors.split("\n"):
                    author = author.replace("*", "").strip()
                    authors_list.append(author.split(",")[0].strip().center(20, " "))
                random.shuffle(authors_list)
                about.extend(authors_list)

            g_vars['about'] = about
            g_vars['result_cache'] = True
            g_vars["disable_keys"] = False

        self.paged_table_obj.display_list_as_paged_table(g_vars, g_vars['about'], title="About")

    def check_for_updates(self, g_vars):

        if g_vars['result_cache'] == False:

            self.alert_obj.display_popup_alert(g_vars, "Checking for updates, please wait...")

            updates = ""
            try:
                g_vars["disable_keys"] = True
                output = subprocess.check_output("/usr/bin/wlanpi-update", shell=True).decode()
                new_packages = subprocess.check_output("echo '" + output + "' | grep ^wlanpi- | awk '{ print $1\":\"$2 }' | sed 's/\/.*:/:/g'", shell=True).decode().strip()
                if len(new_packages) > 0:
                    updates = new_packages.split('\n')
            except:
                updates = None
            finally:
                g_vars["disable_keys"] = False

            g_vars['updates'] = updates
            g_vars['result_cache'] = True

        updates = g_vars['updates']

        if updates == None:
            self.alert_obj.display_alert_error(g_vars, "Failed to check for updates.", title="Error")
        elif len(updates) > 0:
            self.simple_table_obj.display_simple_table(g_vars, g_vars['updates'], title="Updates found")
        else:
            self.alert_obj.display_alert_error(g_vars, "All WLAN Pi packages are up-to-date.", title="No updates found")

    def install_updates(self, g_vars):

        if g_vars['result_cache'] == False:

            self.alert_obj.display_popup_alert(g_vars, "Checking for updates, please wait...")

            try:
                output = subprocess.check_output("/usr/bin/wlanpi-update", shell=True).decode()
                new_packages = subprocess.check_output("echo '" + output + "' | grep ^wlanpi- | awk '{ print $1\":\"$2 }' | sed 's/\/.*:/:/g'", shell=True).decode().strip()
                if len(new_packages) > 0:
                    self.alert_obj.display_popup_alert(g_vars, "Installing updates, please wait...")
                    subprocess.check_output("/usr/bin/wlanpi-update -u", shell=True).decode().strip()
                    self.alert_obj.display_alert_info(g_vars, "Packages updated successfully.", title="Success")
                else:
                    self.alert_obj.display_alert_error(g_vars, "Nothing to update.", title="Install updates")
            except:
                self.alert_obj.display_alert_error(g_vars, "Failed to install updates.", title="Error")
            finally:
                g_vars["disable_keys"] = False

            g_vars['result_cache'] = True
