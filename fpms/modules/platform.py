#
"""
platform.py - platform types and models
"""

PLATFORM_UNKNOWN = "Unknown"
PLATFORM_PRO = "WLAN Pi Pro"
PLATFORM_R4 = "WLAN Pi R4"
PLATFORM_M4 = "WLAN Pi M4"
PLATFORM_M4_PLUS = "WLAN Pi M4+"
PLATFORM_GO = "WLAN Pi Go"

# Kernel labels of the gpiochip wired to the 40-pin header (Pi 3/4/CM4, Pi 5)
HEADER_GPIOCHIP_LABELS = ("pinctrl-bcm2835", "pinctrl-bcm2711", "pinctrl-rp1")
