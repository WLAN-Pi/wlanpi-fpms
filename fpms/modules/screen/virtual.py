#!/usr/bin/env python

import sys

from fpms.modules.screen.screen import AbstractScreen


class Virtual(AbstractScreen):
    """No-op screen backend, used only when no ST7735/SSD1351 display
    hardware is present (or FPMS_DISPLAY=virtual).

    Pages call render_text() to show their content as plain terminal text
    (when stdout is a TTY), so the menu is readable live over SSH. The
    -e emulator's 'g' key still captures full 128x128 PNG screenshots.
    On a machine with a real display this backend is never selected, so
    the terminal text view is not available there.
    """

    def __init__(self):
        self.hints = []
        self._last = None

    def init(self):
        return True

    def drawImage(self, image):
        pass

    def set_hints(self, hints):
        self.hints = list(hints)

    def render_text(self, title, lines):
        if not sys.stdout.isatty():
            return
        # Only redraw when the content actually changes; the main loop
        # re-runs the active page every 2s, so without this every cycle
        # clears and redraws the same frame (flicker).
        key = (title, tuple(lines), tuple(self.hints))
        if key == self._last:
            return
        self._last = key
        # \r\n, not \n: a bare \n advances without returning to column 0,
        # which paints each line progressively indented on terminals that
        # don't translate LF (tmux, real terminals). \x1b[J clears any rows
        # left over when a shorter frame follows a taller one.
        out = ["\x1b[H\x1b[2J", title.upper()]
        for line in lines:
            out.append(line)
        if self.hints:
            out.append("")
            out.extend(self.hints)
        sys.stdout.write("\r\n".join(out) + "\x1b[J")
        sys.stdout.flush()

    def clear(self):
        pass

    def sleep(self):
        pass

    def wakeup(self):
        pass
