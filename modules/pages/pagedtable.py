#################################
# Create a simpe table object
#################################
import modules.wlanpi_oled as oled

from modules.pages.display import *
from modules.constants import (
    STATUS_BAR_HEIGHT,
    SMART_FONT,
    MAX_TABLE_LINES,
)
from modules.themes import (
    THEME
)

class PagedTable(object):

    def __init__(self, g_vars):

        # grab a screeb obj
        self.display_obj = Display(g_vars)
        self.draw = g_vars['draw']

    def display_paged_table(self, g_vars, table_data):
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
        padding = 2
        font_offset = 2
        font_size = 11
        item_length_max = 20
        table_display_max = MAX_TABLE_LINES

        # write title
        title = table_data['title']
        total_pages = len(table_data['pages'])
        g_vars['table_pages'] = total_pages

        if total_pages > 1:
            title += " ({}/{})".format(g_vars['current_scroll_selection'] + 1, total_pages)

        g_vars['draw'].rectangle((x, y, PAGE_WIDTH, STATUS_BAR_HEIGHT), outline=0, fill=THEME.page_table_title_background.value)
        g_vars['draw'].text((x + padding, y + font_offset), title.center(item_length_max,
                                                    " "),  font=SMART_FONT, fill=THEME.page_table_title_foreground.value)

        font_offset += font_size + padding

        # Extract pages data
        table_pages = table_data['pages']
        page_count = len(table_pages)

        # Display the page selected - correct over-shoot of page down
        if g_vars['current_scroll_selection'] >= page_count:
            g_vars['current_scroll_selection'] = page_count - 1

        # Correct over-shoot of page up
        if g_vars['current_scroll_selection'] < 0:
            g_vars['current_scroll_selection'] = 0

        page = table_pages[g_vars['current_scroll_selection']]

        # If the page has greater than table_display_max entries, slice it
        if len(page) > table_display_max:
            page = page[0:table_display_max]

        for item in page:

            if len(item) > item_length_max:
                item = item[0:item_length_max]

            g_vars['draw'].text((x + padding, y + font_offset), item,  font=SMART_FONT, fill=THEME.page_table_row_foreground.value)

            font_offset += font_size

        oled.drawImage(g_vars['image'])

        g_vars['display_state'] = 'page'
        g_vars['drawing_in_progress'] = False

        return


    def display_list_as_paged_table(self, g_vars, item_list, title=''):
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
        table_display_max = MAX_TABLE_LINES

        counter = 0
        while item_list:
            slice = item_list[counter: counter+table_display_max]
            data['pages'].append(slice)
            item_list = item_list[counter+table_display_max:]

        self.display_paged_table(g_vars, data)

        return
