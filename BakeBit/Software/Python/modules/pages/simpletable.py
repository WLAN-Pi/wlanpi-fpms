#################################
# Create a simpe table object
#################################
import bakebit_128_64_oled as oled
from textwrap import wrap

from modules.pages.display import *
from modules.nav.navigation import *
from modules.constants import (
    SMART_FONT,
    FONT11,
)

class SimpleTable(object):

    def __init__(self, g_vars):

        # grab a screeb obj
        self.display_obj = Display(g_vars)

        # grab a navigation obj
        self.nav_button_obj = NavButton(g_vars, 255, SMART_FONT)
        self.draw = g_vars['draw']

    def display_simple_table(self, g_vars, item_list, back_button_req=0, title='', font="small"):
        '''
        This function takes a list and paints each entry as a line on a
        page. It also displays appropriate up/down scroll buttons if the
        entries passed exceed a page length (one line at a time)
        '''

        g_vars['drawing_in_progress'] = True
        g_vars['display_state'] = 'page'

        # Clear display prior to painting new item
        self.display_obj.clear_display(g_vars)

        y = 0
        x = 0
        font_offset = 0

        if font == "small":
            font_type = SMART_FONT
            font_size = 11
            item_length_max = 20
            table_display_max = 5
        elif font == "medium":
            font_type = FONT11
            font_size = 11
            item_length_max = 17
            table_display_max = 4

        # write title if present
        if title != '':
            g_vars['draw'].text((x, y + font_offset), title.center(item_length_max,
                                                               " "),  font=font_type, fill=255)
            font_offset += font_size
            table_display_max -= 1

        previous_table_list_length = g_vars['table_list_length']
        g_vars['table_list_length'] = len(item_list)

        # if table length changes, reset current scroll selection
        # e.g. when showing lldp table info and eth cable
        # pulled so list size changes
        if g_vars['table_list_length'] != previous_table_list_length:
            g_vars['current_scroll_selection'] = 0

        # if we're going to scroll of the end of the list, adjust pointer
        if g_vars['current_scroll_selection'] + table_display_max > g_vars['table_list_length']:
            g_vars['current_scroll_selection'] -= 1

        # modify list to display if scrolling required
        if g_vars['table_list_length'] > table_display_max:

            table_bottom_entry = g_vars['current_scroll_selection'] + table_display_max
            item_list = item_list[g_vars['current_scroll_selection']: table_bottom_entry]

            # show down if not at end of list in display window
            if table_bottom_entry < g_vars['table_list_length']:
                self.nav_button_obj.down()

            # show an up button if not at start of list
            if g_vars['current_scroll_selection'] > 0:
                self.nav_button_obj.next(function="up")

        for item in item_list:

            if len(item) > item_length_max:
                item = item[0:item_length_max]

            self.draw.text((x, y + font_offset), item,
                            font=font_type, fill=255)

            font_offset += font_size

        # Back button
        if back_button_req:
            self.nav_button_obj.back(function="exit")

        oled.drawImage(g_vars['image'])

        g_vars['display_state'] = 'page'
        g_vars['drawing_in_progress'] = False

        return
    
    def display_dialog_msg(self, g_vars, msg, back_button_req=0, wrap_limit=17, font="medium"):
        '''
        display informational dialog box
        '''

        msg_list = wrap(msg, wrap_limit)
        self.display_simple_table(g_vars, msg_list, back_button_req, title='Info:', font=font)
