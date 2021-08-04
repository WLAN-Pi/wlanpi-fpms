# WLANPi Bettercap Control Script
*Shell script to enable/disable Bettercap for the WLANPi - reference document*

This package is controlled using the menu system detailed in the WLANPi project : [wlanpi-nanohat-oled](https://github.com/WLAN-Pi/wlanpi-nanohat-oled). It is included in the file bundle and installed as part of that bundle. The notes below are only of use for development purposes and are not required to use this feature for the front panel menu system.

## Requirements

To be able to start/stop Bettercap on the WLANPi via the front panel menu, you will need:

 - Bettercap on a WLANPi (installed as part of the std WLANPi distribution)
 - WLANPi distribution v1.7.2 or later installed on a WLANPi (https://github.com/WLAN-Pi/wlanpi/releases), which includes [wlanpi-nanohat-oled.py](https://github.com/WLAN-Pi/wlanpi-nanohat-oled) v0.19 or later

## Installation

This script is installed as part of the front panel menu system bundle installation - see the [project home page](https://github.com/WLAN-Pi/wlanpi-nanohat-oled) for details. 

## Usage

The CLI usage instructions are shown below. These are not generally required, as this batch file is called by the WLANPi menu system. Each command returns a short textual status message to indicate the result of the attempted operation.

```
 cd /home/wlanpi/nanohat-oled-scripts
 
 # check Bettercap status
 ./bettercap_ctl status

 # Start Bettercap
 ./bettercap_ctl start

 # Stop Bettercap
 ./bettercap_ctl stop
```

