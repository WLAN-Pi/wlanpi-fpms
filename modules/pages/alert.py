#################################
# Create an alert object
#################################
import modules.wlanpi_oled as oled
from textwrap import wrap

from modules.pages.display import *
from modules.themes import THEME
from modules.constants import (
    STATUS_BAR_HEIGHT,
    SMART_FONT,
    FONT11,
    MAX_TABLE_LINES,
)

class Alert(object):

    def __init__(self, g_vars):

        # grab a screeb obj
        self.display_obj = Display(g_vars)
        self.draw = g_vars['draw']

    def display_alert(self, g_vars, message, title="Alert",
        title_foreground="white", title_background="black", message_foreground="white"):

        g_vars['drawing_in_progress'] = True
        g_vars['display_state'] = 'page'

        item_list = wrap(message, 17)

        # Clear display prior to painting new item
        self.display_obj.clear_display(g_vars)

        y = 0
        x = 0
        padding = 2
        font_offset = 2

        font_type = FONT11
        font_size = 11
        item_length_max = 20

        # write title if present
        g_vars['draw'].rectangle((x, y, PAGE_WIDTH, STATUS_BAR_HEIGHT), outline=0, fill=title_background)
        g_vars['draw'].text((x + padding, y + font_offset), title.center(item_length_max, " "),  font=SMART_FONT, fill=title_foreground)
        font_offset += font_size + padding

        y += font_offset

        item_length_max = 17

        for item in item_list:

            if len(item) > item_length_max:
                item = item[0:item_length_max]

            self.draw.text((x + padding, y + font_offset), item.center(item_length_max, " "),
                            font=font_type, fill=THEME.alert_message_foreground.value)

            font_offset += font_size

        oled.drawImage(g_vars['image'])

        g_vars['display_state'] = 'page'
        g_vars['drawing_in_progress'] = False

        return

    def display_alert_info(self, g_vars, msg, title="Info"):
        self.display_alert(g_vars, msg, title=title,
            title_foreground=THEME.alert_info_title_foreground.value,
            title_background=THEME.alert_info_title_background.value)

    def display_alert_error(self, g_vars, msg, title="Error"):
            self.display_alert(g_vars, msg, title=title,
                title_foreground=THEME.alert_error_title_foreground.value,
                title_background=THEME.alert_error_title_background.value)
