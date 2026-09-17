#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
        # Fixed output size: the 128x128 frame renders as a compact 64x64 char
        # square (each half-block char covers a 2x2 block of native pixels)
        # regardless of terminal size. Previously it stretched to fill the
        # whole screen.
        cols = 64
        rows = 64
        img = image.convert("RGB").resize((cols, rows * 2), Image.LANCZOS)
        px = img.load()
        out = ["\x1b[H\x1b[2J"]
        for y in range(rows):
            line = []
            for x in range(cols):
                # half-block char: foreground = top pixel, background = bottom
                tr, tg, tb = px[x, y * 2]
                br, bg, bb = px[x, y * 2 + 1]
                line.append(
                    f"\x1b[38;2;{tr};{tg};{tb}m\x1b[48;2;{br};{bg};{bb}m▀"
                )
            out.append("".join(line) + "\x1b[0m")
        sys.stdout.write("\n".join(out))
        sys.stdout.flush()