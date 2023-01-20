[![packagecloud-badge](https://img.shields.io/badge/deb-packagecloud.io-844fec.svg)](https://packagecloud.io/)

# WLAN Pi Front Panel Menu System (FPMS)

This project enables the SPI display of WLAN Pi based on the CM4 hardware.

The original ["fpms" repo](https://github.com/WLAN-Pi/fpms) is only compatible with NEO2 hardware and its NanoHat OLED I2C display.

## Components and Troubleshooting

### Packages 

We are using dh-virtualenv to package the `wlanpi-fpms` Python project into an installable Debian package (`.deb`). The Debian software packages for `wlanpi-fpms` are hosted on Packagecloud and installed automatically on the WLAN Pi OS images.

### Systemd Service

FPMS is now run as a Systemd Service on the WLAN Pi. Systemd is a widely used system manager across Linux distributions.

There is a single primary service for `wlanpi-fpms`:

* `wlanpi-fpms` service which displays information on the SPI display.

You can use `systemctl` to view the status of it:

```bash
systemctl status wlanpi-fpms
```

### Troubleshooting

For troubleshooting, use `systemctl` or `journalctl` to check status or log for the service:

```bash
systemctl status wlanpi-fpms
journalctl -u wlanpi-fpms
```

## Developers

Looking to get your hands dirty?

To install and run `wlanpi-fpms` for development and manual testing refer to the [DEVELOPMENT.md](DEVELOPMENT.md) documentation.

### System requirements

The SPI interface must be enabled for FPMS to work and communicate with the display. 

#### Option 1

Use `raspi-config` to enable SPI:

```
sudo raspi-config
```

#### Option 2

1. Edit boot config: `sudo vim /boot/config.txt`
2. Enable SPI interface by adding this line: `dtparam=spi=on`

## Thanks

`wlanpi-fpms` is built and maintained by a wonderful list of folks found in either [AUTHORS.md](fpms/AUTHORS.md) or the git commit log. If your name is missing, please add yourself and submit a PR.

## OSS

Thank you to all the creators and maintainers of the following open source software used by `wlanpi-fpms`:

* [dh-virtualenv](https://github.com/spotify/dh-virtualenv)
* [GPIO Zero](https://gpiozero.readthedocs.io/en/stable)
* [Luma.OLED](https://luma-oled.readthedocs.io/en/latest)
* [Pillow](https://python-pillow.org)
* [pip-tools](https://github.com/jazzband/pip-tools)
* [Python](https://www.python.org)
* [RPi.GPIO](https://pypi.org/project/RPi.GPIO)
* [python-qrcode](https://github.com/lincolnloop/python-qrcode)
