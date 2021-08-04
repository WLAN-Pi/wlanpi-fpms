# WLAN Pi Front Panel Menu System (FPMS)

This "wlanpi-fpms" project enabled the SPI display of WLAN Pi based on the CM4 hardware.

The original "fpms" repo is only compatible with NEO2 hardware and its NanoHat OLED I2C display.

## Services

"fpms" service displays information on the SPI display.

"networkinfo" service mainly delivers the LLDP and CDP neighbour detection.

To check status of the services, execute:
sudo systemctl status fpms
sudo systemctl status networkinfo

## Hardware requirements

The SPI interface must be enabled for FPMS to work and communicate with the display. "sudo raspi-config" can be used to enable SPI.
