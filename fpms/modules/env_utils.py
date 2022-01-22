"""

    A set of utilities that query vary aspects of the environment in which
    FPMS is running. These will be replcaed by back-end API calls in the
    longer term
"""

import subprocess
import re
import os
import hashlib
import qrcode

from PIL import Image

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

        platform = "pro"

        # get output of cpuinfo
        cpuinfo_cmd = "cat /proc/cpuinfo"
        try:
            cmd_output = subprocess.check_output(cpuinfo_cmd, shell=True).decode()
            cmd_output_list = cmd_output.split('\n')

        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            print("Err: issue running 'cat /proc/cpuinfo' : ", output)
            return "Unknown"

        model = cmd_output_list[-2]

        if not re.search(r'Raspberry', model):
            print("Error in get_platform(): no Raspberry model detected")
            return "Unknown"

        if not re.search(r'Compute Module 4', model):
            platform = "community"

        if os.path.exists("/boot/waveshare"):
            platform = "waveshare"

        return platform

    def get_mode(self, MODE_FILE):

        valid_modes = ['classic', 'wconsole', 'hotspot', 'wiperf', 'server']

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
                    version = value.strip()
                    wlanpi_ver = "WLAN Pi " + version[1:-1]
                    break

        return wlanpi_ver

    def get_hostname(self):

        try:
            hostname = subprocess.check_output('hostname -A', shell=True).decode().strip()
            if hostname == "":
                hostname = subprocess.check_output('hostname', shell=True).decode().strip()
        except:
            hostname = 'Unknown'

        return hostname

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
            qr = qrcode.QRCode(box_size=2, border=3, error_correction=qrcode.constants.ERROR_CORRECT_M)
            qr.add_data(qrcode_spec)
            qr.make(fit=True)
            qr.make_image().save(qrcode_path)

        return qrcode_path
