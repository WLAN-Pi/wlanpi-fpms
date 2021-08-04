#################################################
# Create a page object that renders dispay page
#################################################
import bakebit_128_64_oled as oled

from modules.pages.display import *
from modules.nav.navigation import *
from modules.constants import (
    SMART_FONT,
    FONT11,
    FONTB12,
)

class Page(object):

    def __init__(self, g_vars):

        # grab a screeb obj
        self.display_obj = Display(g_vars)

        # grab a navigation obj
        self.nav_button_obj = NavButton(g_vars, 255, SMART_FONT)

    def draw_page(self, g_vars, menu):

        # Drawing already in progress - return
        if g_vars['drawing_in_progress']:
            return

        # signal we are drawing
        g_vars['drawing_in_progress'] = True

        ################################################
        # show menu list based on current menu position
        ################################################

        # FIXME: This feels clunky. Would be best to access menu locations
        #       via evaluated location rather than crawling over menu

        menu_structure = menu
        location_search = []
        depth = 0
        section_name = [g_vars['home_page_name']]

        # Crawl the menu structure until we hit the current specified location
        while g_vars['current_menu_location'] != location_search:

            # List that will be used to build menu items to display
            menu_list = []

            # Current menu location choice specified in list format:
            #  g_vars['current_menu_location'] = [2,1]
            #
            # As we move though menu depths, inpsect next level of
            # menu structure
            node = g_vars['current_menu_location'][depth]

            # figure out the number of menu options at this menu level
            number_menu_choices = len(menu_structure)

            if node == number_menu_choices:

                # we've fallen off the end of menu choices, fix item by zeroing
                node = 0
                g_vars['current_menu_location'][depth] = 0

            location_search.append(node)

            item_counter = 0

            for menu_item in menu_structure:

                item_name = menu_item['name']

                # this is the currently selected item, pre-pend name with '*'
                if (item_counter == node):
                    section_name.append(item_name)
                    item_name = "*" + item_name

                menu_list.append((item_name))

                item_counter = item_counter + 1

            depth = depth + 1

            # move down to next level of menu structure & repeat for new level
            menu_structure = menu_structure[node]['action']

        option_number_selected = node
        g_vars['option_selected'] = menu_structure

        # if we're at the top of the menu tree, show the home page title
        if depth == 1:
            page_name = g_vars['home_page_name']
        else:
            # otherwise show the name of the parent menu item
            page_name = section_name[-2]

        page_title = ("[ " + page_name + " ]").center(17, " ")

        # Clear display prior to painting new item
        self.display_obj.clear_display(g_vars)

        # paint the page title
        g_vars['draw'].text((1, 1), page_title,  font=FONTB12, fill=255)

        # vertical starting point for menu (under title) & incremental offset for
        # subsequent items
        y = 15
        y_offset = 13

        # define display window limit for menu table
        table_window = 3

        # determine the menu list to show based on current selection and window limits
        if (len(menu_list) > table_window):

            # We've got more items than we can fit in our window, need to slice to fit
            if (option_number_selected >= table_window):
                menu_list = menu_list[(
                    option_number_selected - (table_window - 1)): option_number_selected + 1]
            else:
                # We have enough space for the menu items, so no special treatment required
                menu_list = menu_list[0: table_window]

        # paint the menu items, highlighting selected menu item
        for menu_item in menu_list:

            rect_fill = 0
            text_fill = 255

            # this is selected menu item: highlight it and remove * character
            if (menu_item[0] == '*'):
                rect_fill = 255
                text_fill = 0
                menu_item = menu_item[1:len(menu_item)]

            # convert menu item to std width format with nav indicator
            menu_item = "{:<17}>".format(menu_item)

            g_vars['draw'].rectangle((0, y, 127, y+y_offset), outline=0, fill=rect_fill)
            g_vars['draw'].text((1, y+1), menu_item,  font=FONT11, fill=text_fill)
            y += y_offset

        # add nav buttons
        self.nav_button_obj.down()
        self.nav_button_obj.next()
        self.nav_button_obj.back()
        # Don't show back button at top level of menu
        
        oled.drawImage(g_vars['image'])

        g_vars['drawing_in_progress'] = False
