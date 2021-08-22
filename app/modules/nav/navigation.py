from modules.constants import (
    NAV_BAR_TOP,
)

#################################
# Front panel navigation buttons
#################################
class NavButton(object):

    def __init__(self, g_vars, fill, font):
       
        self.nav_bar_top = NAV_BAR_TOP
        self.font = font
        self.fill = fill
        self.g_vars = g_vars
        
        # figure out key map in use
        self.key_map_name = g_vars.get('key_map')
        self.key_map = g_vars['key_mappings'][self.key_map_name]['key_functions']
        self.map_type = g_vars['key_mappings'][self.key_map_name]['type']
        
    #######################################
    # Rendering of buttons on screen
    #######################################
    def render_button(self, label, position):
        # invert if using symbols
        if self.map_type == 'symbol':
            rect_fill = 255
            self.fill = 0
            self.g_vars['draw'].rectangle((position, self.nav_bar_top, position + 25, self.nav_bar_top + 15), outline=0, fill=rect_fill)
        
        self.g_vars['draw'].text((position, self.nav_bar_top), label, fill=self.fill, font=self.font)
        return


    def back(self, function="back"):
        pos = self.key_map[function]['position']
        label = self.key_map[function]['label']
        self.render_button(label, pos)
        return


    def next(self, function="next"):
        pos = self.key_map[function]['position']
        label = self.key_map[function]['label']
        self.render_button(label, pos)
        return


    def down(self, function="down"):
        pos = self.key_map[function]['position']
        label = self.key_map[function]['label']
        self.render_button(label, pos)
        return


