# WLAN Pi Front Panel Menu System (FPMS)

This project enables the SPI display of WLAN Pi based on the CM4 hardware.

The original ["fpms" repo](https://github.com/WLAN-Pi/fpms) is only compatible with NEO2 hardware and its NanoHat OLED I2C display.

## Services

"fpms" service displays information on the SPI display.

"networkinfo" service mainly delivers the LLDP and CDP neighbour detection.

To check status of the services, execute:
`sudo systemctl status fpms`
`sudo systemctl status networkinfo`

## Hardware requirements

The SPI interface must be enabled for FPMS to work and communicate with the display. `sudo raspi-config` can be used to enable SPI.

## Installation instructions

Currently, "wlanpi-fpms" does not run in a virtual environment, but it is planned for near future. To install it, please follow these instructions.

1. Edit boot config: `sudo nano /boot/config.txt`
2. Enable SPI interface by adding this line: `dtparam=spi=on`
3. Install Luma.OLED: `sudo -H pip3 install --upgrade luma.oled`
4. Clone this repo by: `cd /usr/share/ && sudo git clone https://github.com/WLAN-Pi/wlanpi-fpms.git`
5. Start FPMS: `sudo python3 /usr/share/fpms/BakeBit/Software/Python/bakebit_nanohat_oled.py`
