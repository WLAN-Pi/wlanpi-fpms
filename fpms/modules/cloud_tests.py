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
        Perform a series of connectivity tests to check if connection
          to Aruba Central Cloud is healthy:

        1. Is eth0 port up?
        2. Do we get an IP address via DHCP?
        3. DNS tests:
        3a. Can we resolve address activate.arubanetworks.com?
        3b. Can we resolve address common.cloud.hpe.com?
        3c. Can we resolve address device.arubanetworks.com?
        3d. Can we resolve address images.arubanetworks.com?
        4. Can we ping the WAN check at pqm.arubanetworks.com?
        5. Can we get a response from port 443 on device.arubanetworks.com?
        """

        # ignore any more key presses as this could cause us issues
        g_vars["disable_keys"] = True

        # Has test been run already?
        if g_vars["result_cache"] == False:

            # record test success/fail
            test_fail = False

            # create empty table
            item_list = ["", "", "", "", "", "", "", "", ""]

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

            dns_fail = False

            if not test_fail:
                # https://help.central.arubanetworks.com/latest/documentation/online_help/content/nms/device-mgmt/communication_ports.htm
                # Can we resolve address activate.arubanetworks.com?
                # Can we resolve address common.cloud.hpe.com?
                # Can we resolve address device.arubanetworks.com?
                # Can we resolve address images.arubanetworks.com?

                try:
                    socket.gethostbyname("activate.arubanetworks.com")
                    item_list[2] = "DNS (ACTIVATE): OK"
                except Exception as error:
                    dns_fail = True
                    item_list[2] = "DNS (ACTIVATE): FAIL"

                if not dns_fail:
                    try:
                        socket.gethostbyname("common.cloud.hpe.com")
                        item_list[3] = "DNS (COMMON): OK"
                    except Exception as error:
                        dns_fail = True
                        item_list[3] = "DNS (COMMON): FAIL"
                else:
                    item_list[3] = "DNS (COMMON): SKIP"

                if not dns_fail:
                    try:
                        socket.gethostbyname("device.arubanetworks.com")
                        item_list[4] = "DNS (DEVICE): OK"
                    except Exception as error:
                        dns_fail = True
                        item_list[4] = "DNS (DEVICE): FAIL"
                else:
                    item_list[3] = "DNS (DEVICE): SKIP"

                if not dns_fail:
                    try:
                        socket.gethostbyname("images.arubanetworks.com")
                        item_list[6] = "DNS (IMAGES): OK"
                    except Exception as error:
                        dns_fail = True
                        item_list[6] = "DNS (IMAGES): FAIL"
                else:
                    item_list[3] = "DNS (IMAGES): SKIP"

            if dns_fail:
                test_fail = True

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
                    item_list[7] = "ICMP (PQM): OK"
                else:
                    item_list[7] = "ICMP (PQM): FAIL"
                    test_fail = True

                if not test_fail:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(2)
                        result = sock.connect_ex(("device.arubanetworks.com", 443))
                    except:
                        pass

                    if result == 0:
                        item_list[8] = "PORT (DEVICE): OK"
                    else:
                        item_list[8] = "PORT (DEVICE): FAIL"
                        test_fail = True
                    sock.close()

            # show results
            self.simple_table_obj.display_simple_table(
                g_vars, item_list, title="Aruba Central Cloud"
            )

            # set flag to prevent constant refresh of screen
            g_vars["result_cache"] = True

        # re-enable front panel keys
        g_vars["disable_keys"] = False

    def test_meraki_cloud(self, g_vars):
        """
        Perform a series of connectivity tests to check if connection
          to Cisco Meraki Cloud is healthy:

        1. Is eth0 port up?
        2. Do we get an IP address via DHCP?
        3. Can we resolve address?
        4. Can we ping the WAN?
        5. Can we get a response from port 443?

        Docs: https://documentation.meraki.com/General_Administration/Other_Topics/Upstream_Firewall_Rules_for_Cloud_Connectivity

        Primary connection uses UDP port 7351 for the tunnel. APs will attempt to use HTTP/HTTPS if unable to connect over port 7351.

        APs perform connnection tests:
        - ping 8.8.8.8
        - ARP gateway
        - DNS resolution

        """
        def get_default_gateway():
            try:
                result = subprocess.check_output("ip route | awk '/default/ {print $3}'", shell=True, text=True).strip()
                return result
            except subprocess.CalledProcessError:
                return None

        def test_udp_connectivity(host, port, timeout=2):
            try:
                command = ["nc", "-uz", host, str(port)]
                result = subprocess.run(command, shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout, text=True)
                if result.returncode == 0:
                    return True
                else:
                    return False
            except subprocess.TimeoutExpired:
                return False
            except Exception as e:
                print(f"Error occurred: {e}")
                return False

        def test_tcp_connectivity(ip, port, timeout=2):
            try:
                sock = socket.create_connection((ip, port), timeout)
                sock.close()
                return True
            except Exception:
                return False

        def test_ping(host, timeout=2):
            try:
                subprocess.check_call(f"ping -c1 -W{timeout} -4 -q {host}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except subprocess.CalledProcessError:
                return False

        # Ignore any more key presses as this could cause us issues
        g_vars["disable_keys"] = True

        # Has test been run already?
        if g_vars["result_cache"] == False:

            # Record test success/fail
            test_fail = False

            gateway_ip = get_default_gateway()

            # Create empty table
            item_list = ["", "", "", "", "", "", "", ""]

            self.alert_obj.display_popup_alert(g_vars, "Running...")

            # Is eth0 up?
            cmd = "/sbin/ethtool eth0 | awk '/Link detected/ {print $3}'"
            result = subprocess.check_output(cmd, shell=True).decode().strip()

            if result == "yes":
                item_list[0] = "Eth0 Port Up: YES"
            elif result == "no":
                item_list[0] = "Eth0 Port Up: NO"
                test_fail = True
            else:
                item_list[0] = "Eth0 Port Up: Unknown"
                test_fail = True

            # We're done if test failed
            if not test_fail:
                # Have we got an IP address?
                cmd = "ip address show eth0 | awk '/inet / {print $2}' | awk -F'/' '{print $1}'"
                result = subprocess.check_output(cmd, shell=True).decode().strip()

                if result:
                    item_list[1] = "MyIP: {}".format(result)
                else:
                    item_list[1] = "MyIP: None"
                    test_fail = True

            if not test_fail:
                if test_udp_connectivity("64.62.142.12", 7351):
                    item_list[2] = "Cloud UDP 7351: OK"
                else:
                    test_fail = True
                    item_list[2] = "Cloud UDP 7351: FAIL"

                if test_udp_connectivity("pool.ntp.org", 123):
                    item_list[3] = "NTP UDP 123: OK"
                else:
                    item_list[3] = "NTP UDP 123: FAIL"
                    test_fail = True

                if test_tcp_connectivity("158.115.128.12", 80):
                    item_list[4] = "Backup TCP 80: OK"
                else:
                    test_fail = True
                    item_list[4] = "Backup TCP 80: FAIL"

                if test_tcp_connectivity("158.115.128.12", 443):
                    item_list[5] = "Backup TCP 443: OK"
                else:
                    test_fail = True
                    item_list[5] = "Backup TCP 443: FAIL"

                if test_ping("8.8.8.8"):
                    item_list[6] = "Ping 8.8.8.8: OK"
                else:
                    test_fail = True
                    item_list[6] = "Ping 8.8.8.8: FAIL"

                try:
                    socket.gethostbyname("pool.ntp.org")
                    item_list[7] = "DNS UDP 53: OK"
                except Exception as error:
                    test_fail = True
                    item_list[7] = "DNS UDP 53: FAIL"

            # Show results
            self.simple_table_obj.display_simple_table(
                g_vars, item_list, title="Meraki Cloud"
            )

            # Set flag to prevent constant refresh of screen
            g_vars["result_cache"] = True

        # Re-enable front panel keys
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

        # Has test been run already?
        if g_vars["result_cache"] == False:

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
            g_vars["result_cache"] = True

        # re-enable front panel keys
        g_vars["disable_keys"] = False

    def test_ruckus_cloud(self, g_vars):
        """
        Perform a series of connectivity tests to see if Ruckus Cloud is available:

        1. Is eth0 port up?
        2. Do we get an IP address via DHCP?
        3. Can we resolve address ruckus.cloud?
        4. Can get get an http 302 response to https://ruckus.cloud

        """

        # ignore any more key presses as this could cause us issues
        g_vars["disable_keys"] = True

        # Has test been run already?
        if g_vars["result_cache"] == False:

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
                # Can we resolve address ruckus.cloud?
                try:
                    socket.gethostbyname("ruckus.cloud")
                    item_list[2] = "DNS: OK"
                except:
                    test_fail = True
                    item_list[2] = "DNS: FAIL"

            if not test_fail:
                # Can we get an http 200 from https://ruckus.cloud ?
                cmd = (
                    'curl -k -s -L -o /dev/null -w "%{http_code}" https://ruckus.cloud'
                )
                result = subprocess.check_output(cmd, shell=True).decode()

                if result == "200":
                    item_list[3] = "HTTP: OK"
                else:
                    item_list[3] = "HTTP: FAIL"
                    test_fail = True

            # show results
            self.simple_table_obj.display_simple_table(
                g_vars, item_list, title="Ruckus Cloud"
            )

            # set flag to prevent constant refresh of screen
            g_vars["result_cache"] = True

        # re-enable front panel keys
        g_vars["disable_keys"] = False

    def test_extreme_cloud(self, g_vars):
        """
        Perform a series of connectivity tests to check if connection
          to Extreme Cloud IQ is healthy:

        1. Is eth0 port up?
        2. Do we get an IP address via DHCP?
        3. DNS tests:
        3. Can we resolve address all regional extremecloudiq dc?
        4. Can we get a response from port 443 on extremecloudiq?

        """

        # ignore any more key presses as this could cause us issues
        g_vars["disable_keys"] = True

        # Has test been run already?
        if g_vars["result_cache"] == False:

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

            dns_fail = False

            if not test_fail:
                # https://extremeportal.force.com/ExtrArticleDetail?an=000079429&q=Fqdn%20extremecloud%20rdc
                # Can we resolve address fra.extremecloudiq.com

                if not dns_fail:
                    try:
                        socket.gethostbyname("fra.extremecloudiq.com")
                        item_list[2] = "DNS (IMAGES): OK"
                    except Exception as error:
                        dns_fail = True
                        item_list[2] = "DNS (IMAGES): FAIL"
                else:
                    item_list[2] = "DNS (IMAGES): SKIP"

                if dns_fail:
                    test_fail = True

                if not test_fail:
                    # can we connect to https extremecloudiq?
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(2)
                        result = sock.connect_ex(("extremecloudiq.com", 443))
                    except:
                        pass

                    if result == 0:
                        item_list[3] = "PORT (DEVICE): OK"
                    else:
                        item_list[3] = "PORT (DEVICE): FAIL"
                        test_fail = True
                    sock.close()

            # show results
            self.simple_table_obj.display_simple_table(
                g_vars, item_list, title="Extreme Cloud"
            )

            # set flag to prevent constant refresh of screen
            g_vars["result_cache"] = True

        # re-enable front panel keys
        g_vars["disable_keys"] = False
