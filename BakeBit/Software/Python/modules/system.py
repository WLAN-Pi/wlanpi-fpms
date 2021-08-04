import bakebit_128_64_oled as oled
import time
import os
import subprocess
import socket

from modules.pages.display import *
from modules.nav.navigation import *
from modules.pages.simpletable import * 
from modules.constants import (
    MENU_VERSION,
    SMART_FONT,
    FONT12,
    FONTB14,
)

class System(object):

    def __init__(self, g_vars):
       
        # grab a screeb obj
        self.display_obj = Display(g_vars)

        # grab a navigation obj
        self.nav_button_obj = NavButton(g_vars, 255, SMART_FONT)

        # create simple table
        self.simple_table_obj = SimpleTable(g_vars)
    
    def shutdown(self, g_vars):
        
        self.simple_table_obj.display_dialog_msg(g_vars, 'Shutting down...', back_button_req=0)
        time.sleep(1)

        oled.clearDisplay()
        g_vars['screen_cleared'] = True

        os.system('systemctl poweroff')
        g_vars['shutdown_in_progress'] = True
        return

    def reboot(self, g_vars):
        
        self.simple_table_obj. display_dialog_msg(g_vars, 'Rebooting...', back_button_req=0)
        time.sleep(1)

        oled.drawImage(g_vars['reboot_image'])

        g_vars['screen_cleared'] = True

        os.system('systemctl reboot')
        g_vars['shutdown_in_progress'] = True
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
        tempStr = "CPU TEMP: %sC" % str(tempI)

        results = [
            "IP: " + str(IP),
            str(CPU),
            str(MemUsage),
            str(Disk),
            tempStr
        ]

        # final check no-one pressed a button before we render page
        if g_vars['display_state'] == 'menu':
            return

        self.simple_table_obj.display_simple_table(g_vars, results, back_button_req=1)

        return

    
    def show_date(self, g_vars):
        '''
        Date page - taken from original bakebit script & modified to add TZ
        '''

        g_vars['drawing_in_progress'] = True

        # Clear display prior to painting new item
        self.display_obj.clear_display(g_vars)

        text = time.strftime("%A")
        g_vars['draw'].text((1, 0), text, font=FONT12, fill=255)
        text = time.strftime("%e %b %Y")
        g_vars['draw'].text((1, 13), text, font=FONT12, fill=255)
        text = time.strftime("%X")
        g_vars['draw'].text((1, 26), text, font=FONTB14, fill=255)
        text = time.strftime("%Z")
        g_vars['draw'].text((1, 41), "TZ: " + text, font=FONT12, fill=255)

        # Back button
        self.nav_button_obj.back()

        oled.drawImage(g_vars['image'])

        g_vars['display_state'] = 'page'
        g_vars['drawing_in_progress'] = False
    
    def fpms_version(self, g_vars):
        self.simple_table_obj.display_simple_table(g_vars, ["Menu version:", MENU_VERSION ],  back_button_req=1, font="medium")