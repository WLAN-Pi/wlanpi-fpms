#################################
# Create a simpe table object
#################################
import bakebit_128_64_oled as oled

from modules.pages.display import *
from modules.nav.navigation import *
from modules.constants import (
    SMART_FONT,
)

class PagedTable(object):

    def __init__(self, g_vars):

        # grab a screeb obj
        self.display_obj = Display(g_vars)

        # grab a navigation obj
        self.nav_button_obj = NavButton(g_vars, 255, SMART_FONT)
        self.draw = g_vars['draw']

    def display_paged_table(self, g_vars, table_data, back_button_req=0):
        '''
        This function takes several pages of information and displays on the
        display with appropriate pg up/pg down buttons

        table data is in format:

        data = {
            'title' = 'page title',
            'pages' = [
                    ['Page 1 line 1', Page 1 line 2, 'Page 1 line 3', 'Page 1 line 4'],
                    ['Page 2 line 1', Page 2 line 2, 'Page 2 line 3', 'Page 2 line 4'],
                    ['Page 3 line 1', Page 3 line 2, 'Page 3 line 3', 'Page 3 line 4'],
                    ...etc.
            ]
        }
        '''
        g_vars['drawing_in_progress'] = True
        g_vars['display_state'] = 'page'

        # Clear display prior to painting new item
        self.display_obj.clear_display(g_vars)

        y = 0
        x = 0
        font_offset = 0
        font_size = 11
        item_length_max = 20
        table_display_max = 4

        # write title
        title = table_data['title']
        total_pages = len(table_data['pages'])

        if total_pages > 1:
            title += " ({}/{})".format(g_vars['current_scroll_selection'] + 1, total_pages)

        g_vars['draw'].text((x, y + font_offset), title.center(item_length_max,
                                                    " "),  font=SMART_FONT, fill=255)

        font_offset += font_size

        # Extract pages data
        table_pages = table_data['pages']
        page_count = len(table_pages)

        # Display the page selected - correct over-shoot of page down
        if g_vars['current_scroll_selection'] >= page_count:
            g_vars['current_scroll_selection'] = page_count - 1

        # Correct over-shoot of page up
        if g_vars['current_scroll_selection'] == -1:
            g_vars['current_scroll_selection'] = 0

        page = table_pages[g_vars['current_scroll_selection']]

        # If the page has greater than table_display_max entries, slice it
        if len(page) > table_display_max:
            page = page[0:table_display_max]

        for item in page:

            if len(item) > item_length_max:
                item = item[0:item_length_max]

            g_vars['draw'].text((x, y + font_offset), item,  font=SMART_FONT, fill=255)

            font_offset += font_size

        # if we're going need to scroll through pages, create buttons
        if (page_count > 1):

            # if (g_vars['current_scroll_selection'] < page_count) and (g_vars['current_scroll_selection'] < page_count-1):
            if g_vars['current_scroll_selection'] < page_count-1:
                self.nav_button_obj.down(function="pgdown")

            if (g_vars['current_scroll_selection'] > 0) and (g_vars['current_scroll_selection'] <= page_count - 1):
                self.nav_button_obj.down(function="pgup")

        # Back button
        if back_button_req:
            self.nav_button_obj.back(function="exit")

        oled.drawImage(g_vars['image'])

        g_vars['display_state'] = 'page'
        g_vars['drawing_in_progress'] = False

        return


    def display_list_as_paged_table(self, g_vars, item_list, back_button_req=0, title=''):
        '''
        This function builds on display_paged_table() and creates a paged display
        from a simple list of results. This provides a better experience that the
        simple line-by-line scrolling provided in display_simple_table()

        See display_paged_table() for required data structure
        '''
        data = {}

        data['title'] = title
        data['pages'] = []

        # slice up list in to pages
        table_display_max = 4

        counter = 0
        while item_list:
            slice = item_list[counter: counter+table_display_max]
            data['pages'].append(slice)
            item_list = item_list[counter+table_display_max:]

        self.display_paged_table(g_vars, data, back_button_req)

        return
