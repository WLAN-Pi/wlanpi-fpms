# wlanpi-nanohat-oled-scripts

*Collection of supporting scripts to provide features for wlanpi-nanohat-oled menu options*

This is a collection of control scripts used by the WLANPi front panel menu system. Each script is used to start, stop and display the status of a specific process that is being controlled by the front panel menu.

Each of these bash scripts interact with a different Linux application/process to enable it to be controlled by the front panel menu system.

Each script is very simple, providing a start, stop and status function. The output from each script is a short text message to indicate the process status that may be used in the front panel menu system.

## Scripts

The following scripts are supported to date. Each has its own information page which is linked below:

 - kismet_ctl (https://github.com/WLAN-Pi/wlanpi-nanohat-oled/blob/master/scripts/doc/kismet_ctl.md)
 - bettercap_ctl (https://github.com/WLAN-Pi/wlanpi-nanohat-oled/blob/master/scripts/doc/bettercap_ctl.md)
 - profile_ctl (https://github.com/WLAN-Pi/wlanpi-nanohat-oled/blob/master/scripts/doc/profiler_ctl.md)
 
Note that a minimum version of [wlanpi-nanohat-oled.py](https://github.com/WLAN-Pi/wlanpi-nanohat-oled) v0.21 or later is required to use these controls

## Installation

These scripts are installed as part of the front panel menu system bundle installation - see the [project home page](https://github.com/WLAN-Pi/wlanpi-nanohat-oled) for details. 
