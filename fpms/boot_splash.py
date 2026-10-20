"""Store the frame that fpms-splash (splash/fpms-splash.c) draws early in boot."""

import os

SPLASH_FILE = "/var/lib/wlanpi-fpms/boot-splash"
FAILED_FILE = "/var/lib/wlanpi-fpms/failed-splash"
PANEL_ST7735 = "st7735"
PANEL_SSD1351 = "ssd1351"


def rgb565(image):
    """Pack a 128x128 RGB image the way both panels expect it."""
    rgb = image.convert("RGB").tobytes()
    buf = bytearray(len(rgb) // 3 * 2)
    for i in range(0, len(rgb), 3):
        r, g, b = rgb[i], rgb[i + 1], rgb[i + 2]
        buf[i // 3 * 2] = (r & 0xF8) | (g >> 5)
        buf[i // 3 * 2 + 1] = ((g << 3) & 0xE0) | (b >> 3)
    return bytes(buf)


def save(panel, gpiochip, frame, path=SPLASH_FILE):
    data = f"{panel} {gpiochip}\n".encode() + frame
    try:
        with open(path, "rb") as f:
            if f.read() == data:
                return
    except OSError:
        pass
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


def load(path=SPLASH_FILE):
    with open(path, "rb") as f:
        header, frame = f.read().split(b"\n", 1)
    panel, gpiochip = header.decode().split()
    return panel, gpiochip, frame
