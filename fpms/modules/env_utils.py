"""

    A set of utilities that query vary aspects of the environment in which
    FPMS is running. These will be replcaed by back-end API calls in the
    longer term
"""

import subprocess
import re
import sys
import os
import hashlib
import qrcode

from PIL import Image
from fpms.modules.platform import *

class EnvUtils(object):

    def __init__(self):

        pass

    def get_platform(self):
        '''
        Method to determine which platform we're running on.
        Uses output of "cat /proc/cpuinfo"

        Possible strings seen in the wild:

           Pro:    Raspberry Pi Compute Module 4
           RPi3b+: Raspberry Pi 3 Model B Plus Rev 1.3
           RPi4:   Raspberry Pi 4 Model B Rev 1.1

        Errors sent to stdout, but will not exit on error
        '''

        platform = PLATFORM_UNKNOWN

        # get output of wlanpi-model
        model_cmd = "wlanpi-model -b"
        try:
            model = subprocess.check_output(model_cmd, shell=True).decode().strip()
        except subprocess.CalledProcessError as exc:
            output = exc.model.decode()
            print("Err: issue running 'wlanpi-model -b' : ", model)
            return "Unknown"

        if model.endswith('R4'):
            platform = PLATFORM_R4

        if model.endswith('M4'):
            platform = PLATFORM_M4

        if model.endswith('M4+'):
            platform = PLATFORM_M4_PLUS

        if model.endswith('Pro'):
            platform = PLATFORM_PRO

        return platform

    def get_platform_name(self):

        platform = self.get_platform()

        if platform == PLATFORM_R4:
            return PLATFORM_NAME_R4
        elif platform == PLATFORM_M4:
            return PLATFORM_NAME_M4
        elif platform == PLATFORM_M4_PLUS:
            return PLATFORM_NAME_M4_PLUS
        elif platform == PLATFORM_PRO:
            return PLATFORM_NAME_PRO
        else:
            return PLATFORM_NAME_UNKNOWN

    def get_mode(self, MODE_FILE):

        valid_modes = ['classic', 'wconsole', 'hotspot', 'wiperf', 'server', 'bridge']

        # check mode file exists and read mode...create with classic mode if not
        if os.path.isfile(MODE_FILE):
            with open(MODE_FILE, 'r') as f:
                current_mode = f.readline().strip()

            # send msg to stdout & exit if mode invalid
            if not current_mode in valid_modes:
                print("The mode read from {} is not a valid mode of operation: {}". format(MODE_FILE, current_mode))
                sys.exit()
        else:
            # create the mode file as it does not exist
            with open(MODE_FILE, 'w') as f:
                current_mode = 'classic'
                f.write(current_mode)

        return current_mode

    def get_image_ver(self, WLANPI_IMAGE_FILE):

        wlanpi_ver = "unknown"

        if os.path.isfile(WLANPI_IMAGE_FILE):
            with open(WLANPI_IMAGE_FILE, 'r') as f:
                lines = f.readlines()

            # pull out the version number for the FPMS home page
            for line in lines:
                (name, value) = line.split("=")
                if name=="VERSION":
                    wlanpi_ver = value.strip()
                    break

        return wlanpi_ver

    def get_hostname(self):

        try:
            hostname = subprocess.check_output('/usr/bin/hostname', shell=True).decode().strip()
            if not "." in hostname:
                domain = "local"
                try:
                    output = subprocess.check_output('/usr/bin/hostname -d', shell=True).decode().strip()
                    if len(output) != 0:
                        domain = output
                except:
                    pass
                hostname = f"{hostname}.{domain}"
            return hostname
        except:
            pass

        return None

    def get_wifi_qrcode_for_hostapd(self):
        '''
        Generates and returns the path to a WiFi QR code for the current Hostapd config.
        '''
        cmd = "grep -E '^ssid|^wpa_passphrase' /etc/hostapd/hostapd.conf | cut -d '=' -f2"

        try:
            ssid, passphrase = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip().split("\n")
            return self.get_wifi_qrcode(ssid, passphrase)

        except Exception as e:
            print(e)
            pass

        return None

    def get_wifi_qrcode(self, ssid, passphrase):
        qrcode_spec = "WIFI:S:{};T:WPA;P:{};;".format(ssid, passphrase)
        qrcode_hash = hashlib.sha1(qrcode_spec.encode()).hexdigest()
        qrcode_path = "/tmp/{}.png".format(qrcode_hash)

        if not os.path.exists(qrcode_path):
            qr = qrcode.QRCode(box_size=2, border=2, error_correction=qrcode.constants.ERROR_CORRECT_M)
            qr.add_data(qrcode_spec)
            qr.make(fit=True)
            qr.make_image().save(qrcode_path)

        return qrcode_path


    def get_help_qrcode(self, watermark=''):
        qrcode_spec = "http://userguide.wlanpi.com/"
        qrcode_hash = hashlib.sha1(qrcode_spec.encode()).hexdigest()
        qrcode_path = "/tmp/{}.png".format(qrcode_hash)

        if not os.path.exists(qrcode_path):
            qr = qrcode.QRCode(box_size=2, border=2, error_correction=qrcode.constants.ERROR_CORRECT_M)
            qr.add_data(qrcode_spec)
            qr.make(fit=True)
            img = qr.make_image()

            # Paste watermark
            if os.path.exists(watermark):
                wmark = Image.open(watermark)

                if wmark is not None:
                    # Convert to RGB
                    img = img.convert("RGB")

                    # Calculate size of watermark
                    qr_width, qr_height = img.size
                    max_size = min(qr_width, qr_height) // 5
                    wmark = wmark.resize((max_size, max_size))
                    wmark_width, wmark_height = wmark.size

                    # Calculate position and paste watermark
                    position = ((qr_width - wmark_width) // 2, (qr_height - wmark_height) // 2)
                    img.paste(wmark, position)

            # Cache QR code
            img.save(qrcode_path)

        return qrcode_path
