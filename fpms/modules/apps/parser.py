import os

import textfsm

with open(
    os.path.realpath(os.path.join(os.getcwd(), "modules/apps/iw_scan.textfsm"))
) as f:
    __template = textfsm.TextFSM(f)


def parse(iw_scan_output: str) -> str:
    """
    Returns a string containing a list of wireless networks

    Example:
        bssid,frequency,rssi,ssid
        bssid,frequency,rssi,ssid
        ...
    """

    out = ""
    for details in __template.ParseText(iw_scan_output):
        out += ",".join(details) + "\n"
    return out
