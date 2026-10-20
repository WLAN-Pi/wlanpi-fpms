import fpms.modules.wlanpi_oled as oled
from fpms.modules.constants import (
    FONTB11,
    FONTB12,
    MAX_PAGE_LINES,
    STATUS_BAR_HEIGHT,
)
from fpms.modules.pages.display import *
from fpms.modules.themes import THEME


class Page:
    def __init__(self, g_vars):
        self.display_obj = Display(g_vars)

    def draw_page(self, g_vars, menu):
        if g_vars["drawing_in_progress"]:
            return

        g_vars["drawing_in_progress"] = True

        menu_structure = menu
        location_search: list = []
        depth = 0
        section_name = [g_vars["home_page_name"]]

        while g_vars["current_menu_location"] != location_search:
            menu_list = []

            node = g_vars["current_menu_location"][depth]

            number_menu_choices = len(menu_structure)

            if node == number_menu_choices:
                node = 0
                g_vars["current_menu_location"][depth] = 0

            location_search.append(node)

            item_counter = 0

            for menu_item in menu_structure:
                item_name = menu_item["name"]

                if item_counter == node:
                    section_name.append(item_name)
                    item_name = "*" + item_name

                if type(menu_item["action"]) is list:
                    if len(item_name) > 16:
                        item_name = item_name[:14] + ".."
                    item_name = item_name + ">"

                menu_list.append(item_name)

                item_counter = item_counter + 1

            depth = depth + 1

            menu_structure = menu_structure[node]["action"]

        option_number_selected = node
        g_vars["option_selected"] = menu_structure

        if depth == 1:
            page_name = g_vars["home_page_name"]
        else:
            page_name = section_name[-2]

        page_title = page_name.upper()

        if len(page_title) > 15:
            page_title = page_title[:13] + ".."

        self.display_obj.clear_display(g_vars)

        g_vars["draw"].rectangle(
            (0, 0, PAGE_WIDTH, STATUS_BAR_HEIGHT),
            fill=THEME.page_title_background.value,
        )
        title_size = FONTB12.getbbox(page_title)
        g_vars["draw"].text(
            ((PAGE_WIDTH - title_size[2]) / 2, 0),
            page_title,
            font=FONTB12,
            fill=THEME.page_title_foreground.value,
        )

        g_vars["draw"].line(
            [(4, (STATUS_BAR_HEIGHT / 2)), (8, 4)],
            fill=THEME.page_title_foreground.value,
            width=1,
        )
        g_vars["draw"].line(
            [(4, (STATUS_BAR_HEIGHT / 2)), (8, STATUS_BAR_HEIGHT - 4)],
            fill=THEME.page_title_foreground.value,
            width=1,
        )

        y = STATUS_BAR_HEIGHT + 1
        y_offset = 14

        table_window = MAX_PAGE_LINES

        if len(menu_list) > table_window:
            if option_number_selected >= table_window:
                menu_list = menu_list[
                    (
                        option_number_selected - (table_window - 1)
                    ) : option_number_selected + 1
                ]
            else:
                menu_list = menu_list[0:table_window]

        for menu_item in menu_list:
            nav = False
            sel = False

            rect_fill = THEME.page_item_background.value
            text_fill = THEME.page_item_foreground.value
            icon_fill = THEME.page_icon_foreground.value
            font_type = FONTB11

            if menu_item[-1] == ">":
                nav = True
                menu_item = menu_item[:-1]

            if menu_item[0] == "*":
                sel = True
                rect_fill = THEME.page_selected_item_background.value
                text_fill = THEME.page_selected_item_foreground.value
                icon_fill = THEME.page_selected_item_foreground.value
                menu_item = menu_item[1 : len(menu_item)]

            g_vars["draw"].rectangle((0, y, PAGE_WIDTH, y + y_offset), fill=rect_fill)
            g_vars["draw"].text((12, y), menu_item, font=font_type, fill=text_fill)

            if nav:
                g_vars["draw"].line(
                    [(2, y + (y_offset / 2) - 2), (2, y + (y_offset / 2) - 2)],
                    fill=icon_fill,
                    width=1,
                )
                g_vars["draw"].line(
                    [(2, y + (y_offset / 2)), (2, y + (y_offset / 2))],
                    fill=icon_fill,
                    width=1,
                )
                g_vars["draw"].line(
                    [(2, y + (y_offset / 2) + 2), (2, y + (y_offset / 2) + 2)],
                    fill=icon_fill,
                    width=1,
                )
                g_vars["draw"].line(
                    [(4, y + (y_offset / 2) - 2), (8, y + (y_offset / 2) - 2)],
                    fill=icon_fill,
                    width=1,
                )
                g_vars["draw"].line(
                    [(4, y + (y_offset / 2)), (8, y + (y_offset / 2))],
                    fill=icon_fill,
                    width=1,
                )
                g_vars["draw"].line(
                    [(4, y + (y_offset / 2) + 2), (8, y + (y_offset / 2) + 2)],
                    fill=icon_fill,
                    width=1,
                )
                g_vars["draw"].line(
                    [(PAGE_WIDTH - 4, y + (y_offset / 2)), (PAGE_WIDTH - 8, y + 3)],
                    fill=icon_fill,
                    width=1,
                )
                g_vars["draw"].line(
                    [
                        (PAGE_WIDTH - 4, y + (y_offset / 2)),
                        (PAGE_WIDTH - 8, y + y_offset - 3),
                    ],
                    fill=icon_fill,
                    width=1,
                )
            else:
                if sel:
                    g_vars["draw"].ellipse(
                        (3, y + (y_offset / 2) - 2, 7, y + (y_offset / 2) + 2),
                        fill=icon_fill,
                    )
                else:
                    g_vars["draw"].ellipse(
                        (3, y + (y_offset / 2) - 2, 7, y + (y_offset / 2) + 2),
                        outline=icon_fill,
                    )

            y += y_offset

        oled.render_text(page_title, menu_list)
        oled.drawImage(g_vars["image"])

        g_vars["drawing_in_progress"] = False
