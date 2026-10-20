import types

from fpms.modules.pages.homepage import *
from fpms.modules.pages.page import *
from fpms.modules.pages.simpletable import *


class Button:
    def __init__(self, g_vars, menu):
        self.homepage_obj = HomePage(g_vars)
        self.page_obj = Page(g_vars)

    def _at_home_page(self, g_vars):
        if (
            g_vars["display_state"] == "page"
            and len(g_vars["current_menu_location"]) == 1
        ):
            return True
        else:
            return False

    def _bottom_of_list(self, current_location, menu):
        menu_selection = menu
        leaf = current_location[-1]
        branch = current_location[0:-1]

        for choice in branch:
            menu_selection = menu_selection[choice]["action"]

        try:
            if menu_selection[(leaf + 1)]:
                return False
        except IndexError:
            return True

        return True

    def _length_of_list(self, current_location, menu):
        menu_selection = menu
        branch = current_location[0:-1]

        for choice in branch:
            menu_selection = menu_selection[choice]["action"]

        try:
            return len(menu_selection)
        except IndexError:
            return 0

        return 0

    def _display_top_menu(self, g_vars, menu):
        g_vars["display_state"] = "menu"
        return self.page_obj.draw_page(g_vars, menu)

    def menu_down(self, g_vars, menu):
        if self._at_home_page(g_vars):
            return self._display_top_menu(g_vars, menu)

        if g_vars["display_state"] == "page":
            if g_vars["current_scroll_selection"] < (g_vars["table_pages"] - 1):
                g_vars["current_scroll_selection"] += 1
                g_vars["option_selected"]()
                return

        if g_vars["display_state"] != "menu":
            return

        is_last = self._bottom_of_list(g_vars["current_menu_location"], menu)
        current_selection = g_vars["current_menu_location"].pop()
        current_selection = 0 if is_last else current_selection + 1
        g_vars["current_menu_location"].append(current_selection)

        self.page_obj.draw_page(g_vars, menu)

    def menu_up(self, g_vars, menu):
        if self._at_home_page(g_vars):
            return self._display_top_menu(g_vars, menu)

        if g_vars["display_state"] == "page" and g_vars["current_scroll_selection"] > 0:
            g_vars["current_scroll_selection"] -= 1
            g_vars["option_selected"]()
            return

        if g_vars["display_state"] != "menu":
            return

        index_last_item = (
            self._length_of_list(g_vars["current_menu_location"], menu) - 1
        )
        current_selection = g_vars["current_menu_location"].pop()
        if current_selection == 0:
            current_selection = index_last_item
        else:
            current_selection = current_selection - 1
        g_vars["current_menu_location"].append(current_selection)

        self.page_obj.draw_page(g_vars, menu)

    def menu_right(self, g_vars, menu):
        if self._at_home_page(g_vars):
            return self._display_top_menu(g_vars, menu)

        if type(g_vars["option_selected"]) is list:
            g_vars["current_menu_location"].append(0)
            self.page_obj.draw_page(g_vars, menu)

    def menu_left(self, g_vars, menu):
        if g_vars["display_state"] == "page":
            g_vars["current_scroll_selection"] = 0
            g_vars["table_list_length"] = 0
            g_vars["display_state"] = "menu"
            g_vars["result_cache"] = False
            g_vars["scan_file"] = ""
            g_vars["ufw_info"] = None
            self.page_obj.draw_page(g_vars, menu)
            return

        if g_vars["display_state"] == "menu":
            if len(g_vars["current_menu_location"]) == 1:
                g_vars["start_up"] = True
                g_vars["current_menu_location"] = [0]
                self.homepage_obj.home_page(g_vars, menu)
            else:
                g_vars["current_menu_location"].pop()
                self.page_obj.draw_page(g_vars, menu)
        else:
            g_vars["display_state"] = "menu"
            self.page_obj.draw_page(g_vars, menu)

    def menu_center(self, g_vars, menu):
        if self._at_home_page(g_vars):
            g_vars["home_page_alternate"] = not g_vars["home_page_alternate"]
            self.homepage_obj.home_page(g_vars, menu)
        else:
            if type(g_vars["option_selected"]) is list:
                g_vars["current_menu_location"].append(0)
                self.page_obj.draw_page(g_vars, menu)
            elif isinstance(g_vars["option_selected"], types.FunctionType):
                g_vars["display_state"] = "page"
                g_vars["option_selected"]()

    def shortcut(self, g_vars, menu, shortcut):
        g_vars["result_cache"] = False
        g_vars["ufw_info"] = None

        if len(shortcut) == 0:
            return

        if isinstance(shortcut[-1], types.FunctionType):
            g_vars["current_menu_location"] = shortcut[:-1]
            g_vars["display_state"] = "page"
            g_vars["option_selected"] = shortcut[-1]
            g_vars["option_selected"]()
        else:
            g_vars["current_menu_location"] = shortcut
            g_vars["current_menu_location"].append(0)
            g_vars["display_state"] = "menu"
            self.page_obj.draw_page(g_vars, menu)
