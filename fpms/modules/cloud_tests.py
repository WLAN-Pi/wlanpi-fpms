import subprocess
import socket

from fpms.modules.pages.alert import *
from fpms.modules.pages.simpletable import *


class CloudUtils(object):
    def __init__(self, g_vars):

        # create simple table object to show dialog & results on display
        self.simple_table_obj = SimpleTable(g_vars)

        # create alert
        self.alert_obj = Alert(g_vars)

    def test_aruba_cloud(self, g_vars):
        """
        Perform a series of connectivity tests to see if Aruba Central Cloud available:

        1. Is eth0 port up?
        2. Do we get an IP address via DHCP?
        3a. Can we resolve address common.cloud.hpe.com
        3b. Can we resolve address device.arubanetworks.com
        4. Can we ping the WAN check? pqm.arubanetworks.com
        """

        # ignore any more key presses as this could cause us issues
        g_vars["disable_keys"] = True

        # Has speedtest been run already?
        if g_vars["speedtest_status"] == False:

            # record test success/fail
            test_fail = False

            # create empty table
            item_list = ["", "", "", "", "", "", "", ""]

            self.alert_obj.display_popup_alert(g_vars, "Running...")

            # Is eth0 up?
            cmd = "/sbin/ethtool eth0 | grep 'Link detected'| awk '{print $3}'"
            result = subprocess.check_output(cmd, shell=True).decode().strip()

            if result == "yes":
                item_list[0] = "Eth0 Port Up: YES"
            elif result == "no":
                item_list[0] = "Eth0 Port Up: NO"
                test_fail = True
            else:
                item_list[0] = "Eth0 Port Up: Unknown"
                test_fail = True

            # we're done if test failed
            if not test_fail:
                # Have we got an IP address?
                cmd = "ip address show eth0 | grep 'inet ' | awk '{print $2}' | awk -F'/' '{print $1}'"
                result = subprocess.check_output(cmd, shell=True).decode().strip()

                if result:
                    item_list[1] = "MyIP: {}".format(result)
                else:
                    item_list[1] = "MyIP: None"
                    test_fail = True

            if not test_fail:
                # Can we resolve address common.cloud.hpe.com?
                # Can we resolve address device.arubanetworks.com?
                # Can we resolve address images.arubanetworks.com?

                try:
                    socket.gethostbyname("common.cloud.hpe.com")
                    item_list[2] = "DNS (ACTIVATE): OK"
                except Exception as error:
                    test_fail = True
                    item_list[2] = "DNS (ACTIVATE): FAIL"

                try:
                    socket.gethostbyname("device.arubanetworks.com")
                    item_list[3] = "DNS (DEVICE): OK"
                except Exception as error:
                    test_fail = True
                    item_list[3] = "DNS (DEVICE): FAIL"

                try:
                    socket.gethostbyname("images.arubanetworks.com")
                    item_list[4] = "DNS (IMAGES): OK"
                except Exception as error:
                    test_fail = True
                    item_list[4] = "DNS (IMAGES): FAIL"

            if not test_fail:
                # Can we get an ICMP response from https://pqm.arubanetworks.com?
                cmd = ["ping", "-c", "2", "-W", "2", "pqm.arubanetworks.com"]
                result = subprocess.run(
                    cmd,
                    shell=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                if result.returncode == 0:
                    item_list[5] = "ICMP (PQM): OK"
                else:
                    item_list[5] = "ICMP (PQM): FAIL"
                    test_fail = True

                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    result = sock.connect_ex(("device.arubanetworks.com", 443))
                except:
                    pass

                if result == 0:
                    item_list[7] = "PORT (DEVICE): OK"
                else:
                    item_list[7] = "PORT (DEVICE): FAIL"
                    test_fail = True
                sock.close()

            # show results
            self.simple_table_obj.display_simple_table(
                g_vars, item_list, title="Aruba Central Cloud"
            )

            # set flag to prevent constant refresh of screen
            g_vars["speedtest_status"] = True

        # re-enable front panel keys
        g_vars["disable_keys"] = False

    def test_mist_cloud(self, g_vars):
        """
        Perform a series of connectivity tests to see if Mist cloud available:

        1. Is eth0 port up?
        2. Do we get an IP address via DHCP?
        3. Can we resolve address  ep-terminator.mistsys.net
        4. Can get get a http 200 response to https://ep-terminator.mistsys.net/about

        """

        # ignore any more key presses as this could cause us issues
        g_vars["disable_keys"] = True

        # Has speedtest been run already?
        if g_vars["speedtest_status"] == False:

            # record test success/fail
            test_fail = False

            # create empty table
            item_list = ["", "", "", ""]

            self.alert_obj.display_popup_alert(g_vars, "Running...")

            # Is eth0 up?
            cmd = "/sbin/ethtool eth0 | grep 'Link detected'| awk '{print $3}'"
            result = subprocess.check_output(cmd, shell=True).decode().strip()

            if result == "yes":
                item_list[0] = "Eth0 Port Up: YES"
            elif result == "no":
                item_list[0] = "Eth0 Port Up: NO"
                test_fail = True
            else:
                item_list[0] = "Eth0 Port Up: Unknown"
                test_fail = True

            # we're done if test failed
            if not test_fail:
                # Have we got an IP address?
                cmd = "ip address show eth0 | grep 'inet ' | awk '{print $2}' | awk -F'/' '{print $1}'"
                result = subprocess.check_output(cmd, shell=True).decode().strip()

                if result:
                    item_list[1] = "MyIP: {}".format(result)
                else:
                    item_list[1] = "MyIP: None"
                    test_fail = True

            if not test_fail:
                # Can we resolve address ep-terminator.mistsys.net?
                try:
                    socket.gethostbyname("ep-terminator.mistsys.net")
                    item_list[2] = "DNS: OK"
                except:
                    test_fail = True
                    item_list[2] = "DNS: FAIL"

            if not test_fail:
                # Can we get an http 200 from https://ep-terminator.mistsys.net/about ?
                cmd = 'curl -k -s -o /dev/null -w "%{http_code}" https://ep-terminator.mistsys.net/about'
                result = subprocess.check_output(cmd, shell=True).decode()

                if result == "200":
                    item_list[3] = "HTTP: OK"
                else:
                    item_list[3] = "HTTP: FAIL"
                    test_fail = True

            # show results
            self.simple_table_obj.display_simple_table(
                g_vars, item_list, title="Mist Cloud"
            )

            # set flag to prevent constant refresh of screen
            g_vars["speedtest_status"] = True

        # re-enable front panel keys
        g_vars["disable_keys"] = False
