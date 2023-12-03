#################################
# Create a simpe table object
#################################
import fpms.modules.wlanpi_oled as oled

from fpms.modules.pages.display import *
from fpms.modules.pages.utils import *
from fpms.modules.themes import THEME
from fpms.modules.constants import (
    STATUS_BAR_HEIGHT,
    SMART_FONT,
    MAX_TABLE_LINES,
)

class PagedTable(object):

    def __init__(self, g_vars):

        # grab a screeb obj
        self.display_obj = Display(g_vars)
        self.draw = g_vars['draw']
        self.string_formatter = StringFormatter()

    def display_paged_table(self, g_vars, table_data, justify=True):
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

        # Gather total pages
        total_pages = len(table_data['pages'])
        g_vars['table_pages'] = total_pages

        y = 0
        x = 0
        padding = 2
        font_offset = 2
        font_size = 11
        item_length_max = 21
        title_length_max = 17
        table_display_max = MAX_TABLE_LINES
        multi_page = True if total_pages > 1 else False

        # Write title
        title = table_data['title']

        # Check if drawing up/down nav indicators
        if multi_page:
            title_length_max -= 1

        # Shorten title if necessary
        if len(title) > title_length_max:
            title = title[:title_length_max-2] + ".."

        # Draw title
        g_vars['draw'].rectangle((x, y, PAGE_WIDTH, STATUS_BAR_HEIGHT), fill=THEME.page_table_title_background.value)
        title_size = SMART_FONT.getbbox(title)
        g_vars['draw'].text((x + (PAGE_WIDTH - title_size[2])/2, y + font_offset), title,  font=SMART_FONT, fill=THEME.page_table_title_foreground.value)

        # Draw back nav indicator
        g_vars['draw'].line([(2, (STATUS_BAR_HEIGHT/2)), (6, 4)], fill=THEME.page_table_title_foreground.value, width=1)
        g_vars['draw'].line([(2, (STATUS_BAR_HEIGHT/2)), (6, STATUS_BAR_HEIGHT-4)], fill=THEME.page_table_title_foreground.value, width=1)

        # Draw up/down nav indicators
        if multi_page:
            current_page = g_vars['current_scroll_selection'] + 1
            up_fill_color = THEME.page_table_disabled_title_foreground.value if current_page == 1 else THEME.page_table_title_foreground.value
            down_fill_color = THEME.page_table_disabled_title_foreground.value if current_page == total_pages else THEME.page_table_title_foreground.value
            # draw up nav indicator
            g_vars['draw'].line([(PAGE_WIDTH - 7, 2), (PAGE_WIDTH - 3, (STATUS_BAR_HEIGHT/2)-2)], fill=up_fill_color, width=1)
            g_vars['draw'].line([(PAGE_WIDTH - 7, 2), (PAGE_WIDTH - 11, (STATUS_BAR_HEIGHT/2)-2)], fill=up_fill_color, width=1)
            # draw down nav indicator
            g_vars['draw'].line([(PAGE_WIDTH - 7, STATUS_BAR_HEIGHT-2), (PAGE_WIDTH - 3, (STATUS_BAR_HEIGHT/2)+2)], fill=down_fill_color, width=1)
            g_vars['draw'].line([(PAGE_WIDTH - 7, STATUS_BAR_HEIGHT-2), (PAGE_WIDTH - 11, (STATUS_BAR_HEIGHT/2)+2)], fill=down_fill_color, width=1)

        font_offset += font_size + padding + padding

        # Extract pages data
        table_pages = table_data['pages']
        page_count = len(table_pages)

        # Display the page selected - correct over-shoot of page down
        if g_vars['current_scroll_selection'] >= page_count:
            g_vars['current_scroll_selection'] = page_count - 1

        # Correct over-shoot of page up
        if g_vars['current_scroll_selection'] < 0:
            g_vars['current_scroll_selection'] = 0

        # Display current page (if there are pages to display)
        if page_count > 0:
            page = table_pages[g_vars['current_scroll_selection']]

            # If the page has greater than table_display_max entries, slice it
            #if len(page) > table_display_max:
            #    page = page[0:table_display_max]

            for item in page:

                if len(item) > item_length_max:
                    item = item[0:item_length_max]

                if justify:
                    item = self.string_formatter.justify(item, width=item_length_max)

                if item == "---":
                    g_vars['draw'].line([(x, y + font_offset + 2), (PAGE_WIDTH, y + font_offset + 2)], fill=THEME.page_table_row_separator.value)
                    font_offset += 3
                else:
                    g_vars['draw'].text((x, y + font_offset), item,  font=SMART_FONT, fill=THEME.page_table_row_foreground.value)
                    font_offset += font_size


        # Draw scroll bars
        if multi_page:
            scroll_bar_length = (PAGE_HEIGHT - STATUS_BAR_HEIGHT - 4) / total_pages
            x = PAGE_WIDTH - 1
            y = STATUS_BAR_HEIGHT + 2 + (scroll_bar_length * (current_page - 1))
            g_vars['draw'].line([(x, y), (x, y+scroll_bar_length)], fill=THEME.page_table_scrollbar.value, joint="curve")

        oled.drawImage(g_vars['image'])

        g_vars['display_state'] = 'page'
        g_vars['drawing_in_progress'] = False

        return


    def display_list_as_paged_table(self, g_vars, item_list, title='', justify=True):
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

        # count separators
        separator_count = 0
        for item in item_list:
            if item == "---":
                separator_count = separator_count + 1

        # adjust max number of lines
        table_display_max = table_display_max + separator_count

        # split long lines
        item_list = self.string_formatter.split(item_list)

        while item_list:
            slice = item_list[:table_display_max]
            data['pages'].append(slice)
            item_list = item_list[table_display_max:]

        self.display_paged_table(g_vars, data, justify=justify)

        return
