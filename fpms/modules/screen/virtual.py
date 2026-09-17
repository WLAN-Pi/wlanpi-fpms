#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from fpms.modules.screen.screen import AbstractScreen


class Virtual(AbstractScreen):
    """No-op screen backend for machines without display hardware.

    Pages call render_text() to show their content as plain terminal text
    (when stdout is a TTY), so the menu is readable live over SSH. The
    -e emulator's 'g' key still captures full 128x128 PNG screenshots.
    """

    def init(self):
        return True

    def drawImage(self, image):
        pass

    def render_text(self, title, lines):
        if not sys.stdout.isatty():
            return
        out = ["\x1b[H\x1b[2J", title.upper()]
        for line in lines:
            out.append(line)
        sys.stdout.write("\n".join(out))
        sys.stdout.flush()

    def clear(self):
        pass

    def sleep(self):
        pass

    def wakeup(self):
        pass