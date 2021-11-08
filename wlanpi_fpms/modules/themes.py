# -*- coding: utf-8 -*-
#
"""
themes.py - display themes
"""

from enum import Enum
from wlanpi_fpms.modules.env_utils import EnvUtils

env_util = EnvUtils()
PLATFORM = env_util.get_platform()

class BlackAndWhiteTheme(Enum):
    display_background            = "black"
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
    alert_info_title_foreground   = "black"
    alert_info_title_background   = "white"
    alert_error_title_foreground  = "black"
    alert_error_title_background  = "white"
    alert_message_foreground      = "white"
    alert_popup_foreground        = "white"
    alert_popup_background        = "black"

class LightTheme(Enum):
    display_background            = "#e4e2e0"
    text_foreground               = "black"
    text_background               = "white"
    status_bar_foreground         = "white"
    status_bar_background         = "#0071bc"
    page_title_foreground         = "white"
    page_title_background         = "#205493"
    page_item_foreground          = "black"
    page_item_background          = "#e4e2e0"
    page_selected_item_foreground = "black"
    page_selected_item_background = "#f9c642"
    page_table_title_foreground   = "black"
    page_table_title_background   = "#f9c642"
    page_table_row_foreground     = "black"
    page_table_row_background     = "#e4e2e0"
    simple_table_title_foreground = "black"
    simple_table_title_background = "#f9c642"
    simple_table_row_foreground   = "black"
    simple_table_row_background   = "#e4e2e0"
    alert_info_title_foreground   = "white"
    alert_info_title_background   = "#2e8540"
    alert_error_title_foreground  = "white"
    alert_error_title_background  = "#cd2026"
    alert_message_foreground      = "black"
    alert_popup_foreground        = "white"
    alert_popup_background        = "black"

class DarkTheme(Enum):
    display_background            = "black"
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
    alert_info_title_foreground   = "white"
    alert_info_title_background   = "#2e8540"
    alert_error_title_foreground  = "white"
    alert_error_title_background  = "#cd2026"
    alert_message_foreground      = "white"
    alert_popup_foreground        = "white"
    alert_popup_background        = "#5b616b"

if PLATFORM == "pro":
    THEME = DarkTheme
else:
    THEME = BlackAndWhiteTheme
