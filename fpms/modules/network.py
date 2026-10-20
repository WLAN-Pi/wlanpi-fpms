import os
import re
import subprocess
from typing import NamedTuple

import fpms.modules.wlanpi_oled as oled
from fpms.modules.constants import (
    CDPNEIGH_FILE,
    ETHTOOL_FILE,
    IFCONFIG_FILE,
    IP_FILE,
    IPCONFIG_FILE,
    IW_FILE,
    LLDPNEIGH_FILE,
    PUBLICIP6_CMD,
    PUBLICIP_CMD,
)
from fpms.modules.pages.alert import Alert
from fpms.modules.pages.display import Display
from fpms.modules.pages.pagedtable import PagedTable
from fpms.modules.pages.simpletable import SimpleTable


class IwInterface(NamedTuple):
    phy: str
    name: str
    type: str
    netns: str


def freq_to_channel(freq_mhz):
    if freq_mhz == 2484:
        return 14
    elif freq_mhz >= 2412 and freq_mhz <= 2484:
        return int(((freq_mhz - 2412) / 5) + 1)
    elif freq_mhz >= 5160 and freq_mhz <= 5885:
        return int(((freq_mhz - 5180) / 5) + 36)
    elif freq_mhz >= 5955 and freq_mhz <= 7115:
        return int(((freq_mhz - 5955) / 5) + 1)

    return None


def netns_cmd(netns, cmd):
    """
    Prefix an argv list so it runs inside the named network namespace
    (netns "" is the root namespace and returns cmd unchanged).
    """
    return [IP_FILE, "netns", "exec", netns, *cmd] if netns else cmd


def read_sysfs(netns, path):
    """
    Read a sysfs file as seen from the given netns. `ip netns exec` remounts
    /sys, so a namespaced interface's entries are only visible from inside it.
    """
    if not netns:
        with open(path) as f:
            return f.read().strip()
    return (
        subprocess.check_output(netns_cmd(netns, ["cat", path]), timeout=5)
        .decode()
        .strip()
    )


def netns_outputs(cmd, timeout=5):
    """
    Return [(netns, output of cmd), ...] for the root namespace (netns "")
    and every named netns. wlanpi-core can move a whole phy into a named netns,
    which hides its interfaces from root. A root failure raises as before; a
    named netns whose exec fails is skipped so one broken namespace cannot hide
    the others.
    """
    outputs = [
        (
            "",
            subprocess.check_output(
                cmd, stderr=subprocess.STDOUT, timeout=timeout
            ).decode(),
        )
    ]

    try:
        netns_list = subprocess.check_output(
            [IP_FILE, "netns", "list"], stderr=subprocess.DEVNULL, timeout=timeout
        ).decode()
    except Exception:
        return outputs

    # `ip netns list` lines look like "name" or "name (id: 0)"
    for line in netns_list.splitlines():
        if not line.strip():
            continue
        netns = line.split()[0]
        try:
            output = subprocess.check_output(
                netns_cmd(netns, cmd),
                stderr=subprocess.DEVNULL,
                timeout=timeout,
            ).decode()
        except Exception:
            continue
        outputs.append((netns, output))

    return outputs


def iw_dev_outputs(timeout=5):
    """Return [(netns, `iw dev` output), ...] for root and every named netns."""
    return netns_outputs([IW_FILE, "dev"], timeout=timeout)


def interface_lines(netns, ifconfig_info):
    """
    Format `ifconfig -a` output from one namespace as "<status> <name>:<ip>"
    lines. Every named netns has its own loopback, so lo is skipped there.
    """
    lines = []
    for interface_name, interface_info in re.findall(
        r"^(\w+?)\: flags(.*?)RX packets", ifconfig_info, re.DOTALL | re.MULTILINE
    ):
        if netns and interface_name == "lo":
            continue

        status = (
            "▲" if re.search("UP", interface_info, re.MULTILINE) is not None else "▽"
        )

        inet_search = re.search("inet (.+?) ", interface_info, re.MULTILINE)
        if inet_search is None:
            ip_address = "-"

            if re.search(r"(wlan\d+)|(mon\d+)", interface_name, re.MULTILINE):
                try:
                    iw_info = subprocess.check_output(
                        netns_cmd(netns, [IW_FILE, interface_name, "info"]),
                        timeout=5,
                    ).decode()

                    if re.search("type monitor", iw_info, re.MULTILINE):
                        ip_address = "Monitor"
                except Exception:
                    ip_address = "-"
        else:
            ip_address = inet_search.group(1)

        if len(interface_name) > 2:
            short_name = interface_name
            if m := re.search(r".*(\d+).*", interface_name):
                id = m.group(1)
                if interface_name.endswith(id):
                    short_name = f"{interface_name[0]}{id}"
                else:
                    short_name = f"{interface_name[0]}{id}{interface_name[-1]}"
                interface_name = short_name

        lines.append(f"{status} {interface_name}:{ip_address}")
    return lines


class Network:
    def __init__(self, g_vars):
        self.display_obj = Display(g_vars)

        self.simple_table_obj = SimpleTable(g_vars)

        self.paged_table_obj = PagedTable(g_vars)

        self.alert_obj = Alert(g_vars)

    def show_interfaces(self, g_vars):
        """
        Return the list of network interfaces with IP address (if available)
        """

        try:
            outputs = netns_outputs([IFCONFIG_FILE, "-a"])
        except Exception as ex:
            interfaces = ["Err: ifconfig error", str(ex)]
            self.simple_table_obj.display_simple_table(g_vars, interfaces)
            return

        interfaces = []
        for netns, ifconfig_info in outputs:
            lines = interface_lines(netns, ifconfig_info)
            if netns and lines:
                interfaces.append(f"[{netns}]")
            interfaces.extend(lines)

        if g_vars["display_state"] == "menu":
            return

        self.paged_table_obj.display_list_as_paged_table(
            g_vars, interfaces, title="Interfaces"
        )

    def show_wlan_interfaces(self, g_vars):
        """
        Create pages to summarise WLAN interface info
        """

        g_wlan_interfaces_key = "network_wlan_interfaces"

        g_vars["disable_keys"] = True
        g_vars["drawing_in_progress"] = True

        if g_vars["result_cache"]:
            self.paged_table_obj.display_paged_table(
                g_vars,
                {"title": "WLAN Interfaces", "pages": g_vars[g_wlan_interfaces_key]},
            )
            g_vars["disable_keys"] = False
            return None

        interfaces = []
        pages = []

        try:
            interfaces = [
                (netns, interface)
                for netns, output in iw_dev_outputs()
                for interface in re.findall(r"^\s*Interface\s+(\S+)", output, re.M)
            ]
        except Exception:
            pass

        if not interfaces:
            oled.render_text("WLAN Interfaces", ["No WLAN adapter detected"])
            g_vars["display_state"] = "page"
            g_vars["drawing_in_progress"] = False
            g_vars["disable_keys"] = False
            return None

        for netns, interface in interfaces:
            page = []
            page.append(f"Interface: {interface}")
            if netns:
                page.append(f"Netns: {netns}")

            try:
                ethtool_output = (
                    subprocess.check_output(
                        netns_cmd(netns, [ETHTOOL_FILE, "-i", interface])
                    )
                    .decode()
                    .strip()
                )
                if m := re.search(r".*driver:\s+(.*)", ethtool_output):
                    page.append(f"Driver: {m.group(1)}")
            except Exception:
                pass

            try:
                modalias = read_sysfs(
                    netns, f"/sys/class/net/{interface}/device/modalias"
                )
                bus = modalias.split(":")[0]
                if bus == "usb":
                    device_id = modalias.split(":")[1][1:10].replace("p", ":")
                    page.append(f"DevID: {device_id}")
                elif bus == "pci":
                    vendor = read_sysfs(
                        netns, f"/sys/class/net/{interface}/device/vendor"
                    )
                    device = read_sysfs(
                        netns, f"/sys/class/net/{interface}/device/device"
                    )
                    page.append(f"DevID: {vendor}:{device}")
            except Exception:
                pass

            try:
                iw_output = (
                    subprocess.check_output(
                        netns_cmd(netns, [IW_FILE, interface, "info"])
                    )
                    .decode()
                    .strip()
                )

                if m := re.search(r".*addr\s+(.*)", iw_output):
                    page.append(f"Addr: {m.group(1).replace(':', '').upper()}")

                if m := re.search(r".*type\s+(.*)", iw_output):
                    mode = m.group(1)
                    page.append(
                        f"Mode: {mode.capitalize() if not mode.isupper() else mode}"
                    )

                if m := re.search(r".*ssid\s+(.*)", iw_output):
                    page.append(f"SSID: {m.group(1)}")

                if m := re.search(r".*\(([0-9]+)\s+MHz\).*", iw_output):
                    freq = int(m.group(1))
                    page.append(f"Freq (MHz): {freq}")
                    page.append(f"Channel: {freq_to_channel(freq)}")

            except Exception as e:
                print(e)

            pages.append(page)

        self.paged_table_obj.display_paged_table(
            g_vars, {"title": "WLAN Interfaces", "pages": pages}
        )

        g_vars[g_wlan_interfaces_key] = pages
        g_vars["result_cache"] = True
        g_vars["display_state"] = "page"
        g_vars["drawing_in_progress"] = False
        g_vars["disable_keys"] = False

    def show_eth0_ipconfig(self, g_vars):
        """
        Return IP configuration of eth0 including IP, default gateway, DNS servers
        """
        ipconfig_file = IPCONFIG_FILE

        eth0_ipconfig_info = []

        try:
            ipconfig_output = (
                subprocess.check_output([ipconfig_file], stderr=subprocess.DEVNULL)
                .decode()
                .strip()
            )
            ipconfig_info = ipconfig_output.split("\n")

        except subprocess.CalledProcessError as exc:
            output = exc.output.decode()
            ipconfigerror = ["Err: ipconfig command error", output]
            self.simple_table_obj.display_simple_table(g_vars, ipconfigerror)
            return

        for n in ipconfig_info:
            n = n.replace("DHCP server name", "DHCP")
            n = n.replace("DHCP server address", "DHCP IP")
            eth0_ipconfig_info.append(n)

        if g_vars["display_state"] == "menu":
            return

        if len(ipconfig_info) <= 1:
            self.alert_obj.display_alert_error(g_vars, "Eth0 is down or not connected.")
        else:
            self.paged_table_obj.display_list_as_paged_table(
                g_vars, eth0_ipconfig_info, title="Eth0 IP Config"
            )

        return

    def show_vlan(self, g_vars):
        """
        Display untagged VLAN number on eth0
        Todo: Add tagged VLAN info
        """
        lldpneigh_file = LLDPNEIGH_FILE
        cdpneigh_file = CDPNEIGH_FILE

        vlan_info = []

        vlan_cmd = (
            "sudo grep -a VLAN " + lldpneigh_file + " || grep -a VLAN " + cdpneigh_file
        )

        if os.path.exists(lldpneigh_file):
            try:
                vlan_output = subprocess.check_output(vlan_cmd, shell=True).decode()
                vlan_info = vlan_output.split("\n")

                if len(vlan_info) == 0:
                    vlan_info.append("No VLAN found")

            except Exception:
                vlan_info = ["No VLAN found"]

        else:
            vlan_info = ["No VLAN found"]

        if g_vars["display_state"] == "menu":
            return

        self.simple_table_obj.display_simple_table(g_vars, vlan_info, title="Eth0 VLAN")

    def show_lldp_neighbour(self, g_vars):
        """
        Display LLDP neighbour on eth0
        """
        lldpneigh_file = LLDPNEIGH_FILE

        neighbour_info = []
        neighbour_cmd = "sudo cat " + lldpneigh_file

        if os.path.exists(lldpneigh_file):
            try:
                neighbour_output = subprocess.check_output(
                    neighbour_cmd, shell=True
                ).decode()
                neighbour_info = neighbour_output.split("\n")

            except subprocess.CalledProcessError as exc:
                output = exc.output.decode()
                error = ["Err: Neighbour command error", output]
                self.simple_table_obj.display_simple_table(g_vars, error)
                return

        if len(neighbour_info) == 0:
            neighbour_info.append("No neighbour")

        if g_vars["display_state"] == "menu":
            return

        self.paged_table_obj.display_list_as_paged_table(
            g_vars, neighbour_info, title="LLDP Neighbour"
        )

    def show_cdp_neighbour(self, g_vars):
        """
        Display CDP neighbour on eth0
        """
        cdpneigh_file = CDPNEIGH_FILE

        neighbour_info = []
        neighbour_cmd = "sudo cat " + cdpneigh_file

        if os.path.exists(cdpneigh_file):
            try:
                neighbour_output = subprocess.check_output(
                    neighbour_cmd, shell=True
                ).decode()
                neighbour_info = neighbour_output.split("\n")

            except subprocess.CalledProcessError as exc:
                output = exc.output.decode()
                error = ["Err: Neighbour command error", output]
                self.simple_table_obj.display_simple_table(g_vars, error)
                return

        if len(neighbour_info) == 0:
            neighbour_info.append("No neighbour")

        if g_vars["display_state"] == "menu":
            return

        self.paged_table_obj.display_list_as_paged_table(
            g_vars, neighbour_info, title="CDP Neighbour"
        )

    def show_publicip(self, g_vars, ip_version=4):
        """
        Shows public IP address and related details, works with any interface with internet connectivity
        """

        publicip_info = []
        cmd = PUBLICIP6_CMD if ip_version == 6 else PUBLICIP_CMD

        if not g_vars["result_cache"]:
            self.alert_obj.display_popup_alert(
                g_vars,
                "Detecting public " + ("IPv6..." if ip_version == 6 else "IPv4..."),
            )

            try:
                g_vars["disable_keys"] = True
                publicip_output = subprocess.check_output([cmd]).decode().strip()
                publicip_info = publicip_output.split("\n")
                g_vars["publicip_info"] = publicip_info
                g_vars["result_cache"] = True
            except subprocess.CalledProcessError:
                self.alert_obj.display_alert_error(
                    g_vars, "Failed to detect public IP address"
                )
                return
            finally:
                g_vars["disable_keys"] = False

        else:
            publicip_info = g_vars["publicip_info"]
            if len(publicip_info) == 1:
                msg = (
                    "Unable to detect public IPv6 address"
                    if ip_version == 6
                    else "Unable to detect public IPv4 address"
                )
                self.alert_obj.display_alert_error(g_vars, msg)
                return

            title = "Public IPv6" if ip_version == 6 else "Public IPv4"
            self.paged_table_obj.display_list_as_paged_table(
                g_vars, publicip_info, title=title, justify=False
            )
