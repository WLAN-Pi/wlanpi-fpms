from PIL import Image

import fpms.modules.wlanpi_oled as oled

from fpms.modules.themes import THEME
from fpms.modules.constants import (
    PAGE_HEIGHT,
    PAGE_WIDTH,
)

#################################
# Display functions
#################################

class Display(object):

    def __init__(self, g_vars):
        pass

    def clear_display(self, g_vars):
        '''
        Paint display black prior to painting new page
        '''

        # Draw a black filled box to clear the display.
        g_vars['draw'].rectangle((0, 0, PAGE_WIDTH, PAGE_HEIGHT),
            fill=THEME.display_background.value)

        return

    def stamp_qrcode(self, g_vars, qrcode_path, x=0, y=0,
        center_horizontally=True, center_vertically=True, draw_immediately=True):
        '''
        Stamp a QR code on the screen at the given offset
        '''
        img = Image.open(qrcode_path, 'r')
        img_w, img_h = img.size
        x = (PAGE_WIDTH  - img_w) // 2 if center_horizontally else x
        y = (PAGE_HEIGHT - img_h) // 2 if center_vertically   else y
        offset = (x, y)
        g_vars['image'].paste(img, offset)
        if draw_immediately:
            oled.drawImage(g_vars['image'])
