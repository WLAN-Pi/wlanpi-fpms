[![packagecloud-badge](https://img.shields.io/badge/deb-packagecloud.io-844fec.svg)](https://packagecloud.io/)

# WLAN Pi Front Panel Menu System (FPMS)

This project enables the SPI display of WLAN Pi based on the CM4 hardware.

The original ["fpms" repo](https://github.com/WLAN-Pi/fpms) is only compatible with NEO2 hardware and its NanoHat OLED I2C display.

## systemd Service

There are two primary service units for `wlanpi-fpms`:

* `wlanpi-fpms` service which displays information on the SPI display.
* `networkinfo` service which mainly delivers the LLDP and CDP neighbour detection.

For troubleshooting, use `systemctl` to check status of the services:

```
systemctl status wlanpi-fpms
systemctl status networkinfo
```

## Packages 

Debian software packages for `wlanpi-fpms` can be found on Packagecloud here <https://packagecloud.io/app/wlanpi/main/search?q=fpms>.

## Development instructions

Looking to get your hands dirty?

To install and run `wlanpi-fpms` for development and manual testing refer to the [DEVELOPMENT.md](DEVELOPMENT.md) documentation.

## System requirements

The SPI interface must be enabled for FPMS to work and communicate with the display. 

### Option 1

Use `raspi-config` to enable SPI:

```
sudo raspi-config
```

### Option 2

1. Edit boot config: `sudo vim /boot/config.txt`
2. Enable SPI interface by adding this line: `dtparam=spi=on`

## Thanks

`wlanpi-fpms` is built and maintained by a wonderful list of folks found in either [AUTHORS.md](AUTHORS.md) or the git commit log. If your name is missing, please add yourself and submit a PR.
