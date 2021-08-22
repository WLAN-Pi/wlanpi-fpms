import types

from modules.pages.homepage import *
from modules.pages.page import *
from modules.pages.simpletable import * 
from modules.constants import (
    BUTTONS_FILE,
)

class Button(object):

    def __init__(self, g_vars, menu):
       
        self.homepage_obj = HomePage(g_vars)
        self.page_obj = Page(g_vars)
        self.simple_table_obj = SimpleTable(g_vars)

    #######################################
    # Actions taken when butons pressed
    #######################################
    def menu_down(self, g_vars, menu):

        # If we are in a table, scroll down (unless at bottom of list)
        if g_vars['display_state'] == 'page':
            g_vars['current_scroll_selection'] += 1
            return

        # Menu not currently shown, do nothing
        if g_vars['display_state'] != 'menu':
            return

        # pop the last menu list item, increment & push back on
        current_selection = g_vars['current_menu_location'].pop()
        current_selection = current_selection + 1
        g_vars['current_menu_location'].append(current_selection)

        self.page_obj.draw_page(g_vars, menu)


    def menu_right(self, g_vars, menu):

        # make sure we know speedtest is done
        g_vars['speedtest_status'] = False

        # If we are in a table, scroll up (unless at top of list)
        if g_vars['display_state'] == 'page':
            if g_vars['current_scroll_selection'] == 0:
                return
            else:
                g_vars['current_scroll_selection'] -= 1
                return

        # Check if the "action" field at the current location is an
        # array or a function.

        # if we have an array, append the current selection and re-draw menu
        if (type(g_vars['option_selected']) is list):
            g_vars['current_menu_location'].append(0)
            self.page_obj.draw_page(g_vars, menu)
        elif (isinstance(g_vars['option_selected'], types.FunctionType)):
            # if we have a function (dispatcher), execute it
            g_vars['display_state'] = 'page'
            g_vars['option_selected']()


    def menu_left(self, g_vars, menu):

        # If we're in a table we need to exit, reset table scroll counters, reset
        # result cache and draw the menu for our current level
        if g_vars['display_state'] == 'page':
            g_vars['current_scroll_selection'] = 0
            g_vars['table_list_length'] = 0
            g_vars['display_state'] = 'menu'
            self.page_obj.draw_page(g_vars, menu)
            g_vars['result_cache'] = False
            return

        if g_vars['display_state'] == 'menu':

            # check to make sure we aren't at top of menu structure
            if len(g_vars['current_menu_location']) == 1:
                # If we're at the top and hit exit (back) button, revert to start-up state
                g_vars['start_up'] = True
                g_vars['current_menu_location'] = [0]
                self.homepage_obj.home_page(g_vars, menu)
            else:
                g_vars['current_menu_location'].pop()
                self.page_obj.draw_page(g_vars, menu)
        else:
            g_vars['display_state'] = 'menu'
            self.page_obj.draw_page(g_vars, menu)


    def go_up(self, g_vars, menu):

        # executed when the back navigation item is selected
        # (e.g. "Cancel") - this is not a button press action

        g_vars['display_state'] = 'menu'

        if len(g_vars['current_menu_location']) == 1:
            # we must be at top level, do nothing
            return
        else:
            # Take off last level of menu structure to go up
            # Set index to 0 so top menu item selected
            g_vars['current_menu_location'].pop()
            g_vars['current_menu_location'][-1] = 0

            self.page_obj.draw_page(g_vars, menu)
    
    def button_set(self, g_vars, keyword, results):
        with open(BUTTONS_FILE, 'w') as f:
            f.write(keyword)
            g_vars['key_map'] = keyword

        self.simple_table_obj.display_simple_table(g_vars, results, back_button_req=1)

    def buttons_classic(self, g_vars):
            self.button_set(g_vars, 'classic', ['Classic mode',  'selected'])

    def buttons_intuitive(self, g_vars):
        self.button_set(g_vars, 'alt', ['Intuit mode',  'selected'])

    def buttons_symbol(self, g_vars):
        self.button_set(g_vars, 'symbols', ['Symbols mode',  'selected'])
