# -*- coding: utf-8 -*-
#
"""
themes.py - display themes
"""

from enum import Enum
from modules.env_utils import EnvUtils

env_util = EnvUtils()
PLATFORM = env_util.get_platform()

class BlackAndWhiteTheme(Enum):
    text_foreground               = "white"
    text_background               = "black"
    status_bar_foreground         = "black"
    status_bar_background         = "white"
    page_title_background         = "white"
    page_title_foreground         = "black"
    page_item_foreground          = "white"
    page_item_background          = "black"
    page_selected_item_foreground = "black"
    page_selected_item_background = "white"
    page_table_title_foreground   = "black"
    page_table_title_background   = "white"
    page_table_row_foreground     = "white"
    page_table_row_background     = "black"
    simple_table_title_foreground = "black"
    simple_table_title_background = "white"
    simple_table_row_foreground   = "white"
    simple_table_row_background   = "black"

class ProTheme(Enum):
    text_foreground               = "white"
    text_background               = "black"
    status_bar_foreground         = "white"
    status_bar_background         = "#0071bc"
    page_title_foreground         = "white"
    page_title_background         = "#205493"
    page_item_foreground          = "white"
    page_item_background          = "black"
    page_selected_item_foreground = "black"
    page_selected_item_background = "#f9c642"
    page_table_title_foreground   = "black"
    page_table_title_background   = "#f9c642"
    page_table_row_foreground     = "white"
    page_table_row_background     = "black"
    simple_table_title_foreground = "black"
    simple_table_title_background = "#f9c642"
    simple_table_row_foreground   = "white"
    simple_table_row_background   = "black"

if PLATFORM == "pro":
    THEME = ProTheme
else:
    THEME = BlackAndWhiteTheme
