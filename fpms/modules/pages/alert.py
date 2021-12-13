#################################
# Create an alert object
#################################
import time
import fpms.modules.wlanpi_oled as oled
from textwrap import wrap

from fpms.modules.pages.display import *
from fpms.modules.themes import THEME
from fpms.modules.constants import (
    STATUS_BAR_HEIGHT,
    SMART_FONT,
    MAX_TABLE_LINES,
)

class Alert(object):

    def __init__(self, g_vars):

        # grab a screeb obj
        self.display_obj = Display(g_vars)
        self.draw = g_vars['draw']

    def display_alert(self, g_vars, message, title="Alert",
        title_foreground="white", title_background="black", message_foreground="white"):
        '''
        Display an alert in full screen mode
        '''

        g_vars['drawing_in_progress'] = True
        g_vars['display_state'] = 'page'

        item_list = wrap(message, 17)

        # Clear display prior to painting new item
        self.display_obj.clear_display(g_vars)

        y = 0
        x = 0
        padding = 2
        font_offset = 2

        font_type = SMART_FONT
        font_size = 11
        item_length_max = 21

        # write title if present
        self.draw.rectangle((x, y, PAGE_WIDTH, STATUS_BAR_HEIGHT), fill=title_background)
        title_size = SMART_FONT.getsize(title)
        self.draw.text((x + (PAGE_WIDTH - title_size[0])/2, y + font_offset), title,  font=SMART_FONT, fill=title_foreground)
        font_offset += font_size + padding

        y += font_offset

        #item_length_max = 21

        for item in item_list:

            if len(item) > item_length_max:
                item = item[0:item_length_max]

            item_size = font_type.getsize(item)
            self.draw.text((x + (PAGE_WIDTH - item_size[0])/2, y + font_offset), item,
                            font=font_type, fill=THEME.alert_message_foreground.value)

            font_offset += font_size

        oled.drawImage(g_vars['image'])

        g_vars['display_state'] = 'page'
        g_vars['drawing_in_progress'] = False

        return

    def display_alert_info(self, g_vars, msg, title="Info"):
        '''
        Display an alert styled for information messages
        '''
        self.display_alert(g_vars, msg, title=title,
            title_foreground=THEME.alert_info_title_foreground.value,
            title_background=THEME.alert_info_title_background.value)

    def display_alert_error(self, g_vars, msg, title="Error"):
        '''
        Display an alert styled for error messages
        '''
        self.display_alert(g_vars, msg, title=title,
            title_foreground=THEME.alert_error_title_foreground.value,
            title_background=THEME.alert_error_title_background.value)

    def display_popup_alert(self, g_vars, msg, delay=0.5):
        '''
        Display a "pop-up" alert centered on the current screen
        '''

        g_vars['drawing_in_progress'] = True
        g_vars['display_state'] = 'page'

        item_length_max = 17
        item_list = wrap(msg, 13)

        font_offset = 2
        margin = 10
        font_size = SMART_FONT.getsize(msg)[1]

        rect_height = font_size * len(item_list) + (font_offset * 2)

        x = 0
        y = (PAGE_HEIGHT - rect_height) / 2
        self.draw.rectangle((margin, y - (rect_height / 2), PAGE_WIDTH - margin, y + rect_height),
            outline=THEME.alert_popup_foreground.value, fill=THEME.alert_popup_background.value)

        y -= font_offset * (len(item_list) + 2)

        for item in item_list:

            if len(item) > item_length_max:
                item = item[0:item_length_max]

            text_size = SMART_FONT.getsize(item)
            self.draw.text((x + (PAGE_WIDTH - text_size[0])/2, y + font_offset), item,
                font=SMART_FONT, fill=THEME.alert_popup_foreground.value)
            font_offset += font_size

        oled.drawImage(g_vars['image'])

        g_vars['drawing_in_progress'] = False

        time.sleep(delay)
