#!/usr/bin/env python
# -*- coding: utf-8 -*-

import shutil
import sys

from PIL import Image

from fpms.modules.screen.screen import AbstractScreen


class Virtual(AbstractScreen):
    """No-op screen backend for machines without display hardware.

    drawImage renders the frame to the terminal as ANSI half-block art when
    stdout is a TTY, so the menu is visible live over SSH. Screenshots are
    still captured at full 128x128 via the -e emulator's 'g' key.
    """

    def init(self):
        return True

    def drawImage(self, image):
        if sys.stdout.isatty():
            self._render_to_terminal(image)

    def clear(self):
        pass

    def sleep(self):
        pass

    def wakeup(self):
        pass

    @staticmethod
    def _render_to_terminal(image):
        # half-block char is 2 vertical pixels, so scale height to 2x columns
        cols, rows = shutil.get_terminal_size((80, 24))
        if cols < 8 or rows < 4:
            return
        img = image.convert("RGB").resize(
            (cols, rows * 2), Image.LANCZOS
        )
        px = img.load()
        out = ["\x1b[H\x1b[2J"]
        for y in range(rows):
            line = []
            for x in range(cols):
                tr, tg, tb = px[x, y * 2]
                br, bg, bb = px[x, y * 2 + 1]
                line.append(
                    f"\x1b[38;2;{tr};{tg};{tb}m\x1b[48;2;{br};{bg};{bb}m▀"
                )
            out.append("".join(line) + "\x1b[0m")
        sys.stdout.write("\n".join(out))
        sys.stdout.flush()