import json
import re
import subprocess
import time

from fpms.modules.constants import BT_ADAPTER_FILE
from fpms.modules.pages.alert import Alert
from fpms.modules.pages.pagedtable import PagedTable


def bt_adapter():
    """
    The adapter wlanpi-bluetooth uses (hci0 can be a USB dongle), or None.
    Releases without wlanpi-bt-adapter always used hci0. If it fails, hci0
    may not be the adapter bt-timedpair opens, so there is no fallback.
    """
    try:
        adapter = (
            subprocess.check_output(
                [BT_ADAPTER_FILE], stderr=subprocess.DEVNULL, timeout=2
            )
            .decode()
            .strip()
        )
    except FileNotFoundError:
        return "hci0"
    except Exception:
        return None
    # The name goes into shell commands.
    return adapter if re.fullmatch(r"hci\d+", adapter) else None


class Bluetooth:
    def __init__(self, g_vars):
        # fpms creates one per action run, and the adapter can change on
        # hotplug, so resolve it here rather than at import.
        self.adapter = bt_adapter()

        # create paged table
        self.paged_table_obj = PagedTable(g_vars)

        # create alert
        self.alert_obj = Alert(g_vars)

    def bluetooth_present(self):
        """
        We want to use hciconfig here as it works OK when no devices are present
        """
        if self.adapter is None:
            return False
        try:
            cmd = f"hciconfig | grep {self.adapter}"
            subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            return True
        except Exception:
            return False

    def bluetooth_name(self):
        try:
            cmd = (
                f"bt-adapter -a {self.adapter} -i" + "| grep Name | awk '{ print $2 }'"
            )
            name = subprocess.check_output(cmd, shell=True).decode().strip()
            return name
        except Exception:
            return None

    def bluetooth_alias(self):
        try:
            cmd = (
                f"bt-adapter -a {self.adapter} -i" + "| grep Alias | awk '{ print $2 }'"
            )
            alias = subprocess.check_output(cmd, shell=True).decode().strip()
            return alias
        except Exception:
            return None

    def bluetooth_address(self):
        try:
            cmd = (
                f"bt-adapter -a {self.adapter} -i"
                + "| grep Address | awk '{ print $2 }'"
            )
            address = subprocess.check_output(cmd, shell=True).decode().strip()
            return address
        except Exception:
            return None

    def bluetooth_power(self):
        """
        We want to use hciconfig here as it works OK when no devices are present
        """
        try:
            cmd = rf"hciconfig {self.adapter} | grep -E '^\s+UP'"
            subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            return True
        except Exception:
            return False

    def bluetooth_set_power(self, power):
        bluetooth_is_on = self.bluetooth_power()

        if power and bluetooth_is_on:
            return True
        if not power and not bluetooth_is_on:
            return True

        value = 1 if power else 0
        try:
            subprocess.run(
                ["bt-adapter", "-a", self.adapter, "--set", "Powered", str(value)],
                check=True,
            )
        except Exception:
            return False

        # Best effort: the state file is wlanpi-bluetooth's bookkeeping, so a
        # failure here must not be reported as a failure to set the adapter.
        try:
            with open("/etc/wlanpi-bluetooth/state", "w") as f:
                f.write(f"{value}\n")
        except OSError:
            pass

        return True

    def paired_device_objects(self):
        """
        Returns (address, alias) of each device paired on self.adapter,
        indexed by D-Bus object path. Raises if BlueZ can't be read.
        """

        # Not bluetoothctl: it lists its default controller's devices, which
        # need not be self.adapter. Not GetManagedObjects: busctl --json fails
        # on it while BlueZ holds a nearby device's ManufacturerData (a{qv}).
        def bluez_objects():
            return (
                subprocess.check_output(
                    ["busctl", "--system", "tree", "--list", "org.bluez"], timeout=10
                )
                .decode()
                .splitlines()
            )

        def device_paths():
            objects = bluez_objects()
            # Without the adapter, BlueZ is restarting and the listing can't
            # show its pairings.
            if f"/org/bluez/{self.adapter}" not in objects:
                raise RuntimeError(f"BlueZ has not registered {self.adapter}")
            return [
                path
                for path in objects
                if re.fullmatch(rf"/org/bluez/{self.adapter}/dev_[0-9A-F_]+", path)
            ]

        devices = {}
        for path in device_paths():
            try:
                output = subprocess.check_output(
                    [
                        "busctl",
                        "--system",
                        "--json=short",
                        "get-property",
                        "org.bluez",
                        path,
                        "org.bluez.Device1",
                        "Paired",
                        "Address",
                        "Alias",
                    ],
                    timeout=10,
                )
            except subprocess.CalledProcessError:
                # BlueZ drops a device it only saw nearby soon after a scan,
                # maybe since the listing. Paired devices are never dropped.
                if path in device_paths():
                    raise
                continue
            paired, address, alias = (
                json.loads(line)["data"] for line in output.splitlines()
            )
            if paired:
                devices[path] = (address, alias)
        return devices

    def bluetooth_paired_devices(self):
        """
        Returns a dictionary of paired devices, indexed by MAC address
        """

        if not self.bluetooth_present():
            return None

        try:
            devices = self.paired_device_objects()
        except Exception:
            return None
        return dict(devices.values()) or None

    def unpair_all(self, g_vars):
        """
        Removes every pairing on self.adapter. Raises if BlueZ can't be read,
        a removal fails, or a device is still paired after 30 seconds.
        """
        # Removal doesn't always take effect at once (seen on Bullseye), so
        # retry until none are left.
        deadline = time.monotonic() + 30
        adapter_path = f"/org/bluez/{self.adapter}"
        paired = self.paired_device_objects()
        while paired:
            if time.monotonic() > deadline:
                raise TimeoutError("Bluetooth devices still paired")
            self.alert_obj.display_popup_alert(g_vars, "Unpairing existing device...")
            # Remove by object path: with a random address, the path isn't
            # derived from the Address property.
            for path in paired:
                subprocess.run(
                    [
                        "busctl",
                        "--system",
                        "call",
                        "org.bluez",
                        adapter_path,
                        "org.bluez.Adapter1",
                        "RemoveDevice",
                        "o",
                        path,
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                    timeout=10,
                )
            time.sleep(1)
            paired = self.paired_device_objects()

    def bluetooth_status(self, g_vars):
        status = []

        if not self.bluetooth_present():
            self.alert_obj.display_alert_error(g_vars, "Bluetooth adapter not found.")
            g_vars["display_state"] = "page"
            return

        status.append("Name:" + (self.bluetooth_name() or ""))
        status.append("Alias:" + (self.bluetooth_alias() or ""))
        status.append("Addr:" + (self.bluetooth_address() or "").replace(":", ""))

        if self.bluetooth_power():
            status.append("Power:On")
        else:
            status.append("Power:Off")

        paired_devices = self.bluetooth_paired_devices()

        if paired_devices is not None:
            status.append("---")
            status.append("PAIRED DEVICES")
            status.append("---")
            for mac in paired_devices:
                status.append("Name:" + paired_devices[mac])
                status.append("Addr:" + mac.replace(":", ""))

        self.paged_table_obj.display_list_as_paged_table(g_vars, status, title="Status")

        g_vars["display_state"] = "page"

    def bluetooth_pair(self, g_vars):
        if not self.bluetooth_present():
            self.alert_obj.display_alert_error(g_vars, "Bluetooth adapter not found.")
            g_vars["display_state"] = "page"
            return

        ok = False
        alert_msg = None
        if self.bluetooth_set_power(True):
            if not g_vars["result_cache"]:
                # Unpair existing paired devices
                g_vars["disable_keys"] = True
                g_vars["bt_pair_error"] = None
                self.alert_obj.display_popup_alert(g_vars, "Entering pairing mode...")
                try:
                    self.unpair_all(g_vars)
                except Exception:
                    # Never open the pairing window with an old pairing left.
                    # Later runs of this page keep showing the error.
                    g_vars["bt_pair_error"] = "Failed to remove paired devices."
                    alert_msg = g_vars["bt_pair_error"]

                g_vars["result_cache"] = True
                g_vars["disable_keys"] = False

            elif g_vars.get("bt_pair_error"):
                alert_msg = g_vars["bt_pair_error"]

            else:
                try:
                    paired_devices = self.paired_device_objects()
                except Exception:
                    paired_devices = None
                    alert_msg = "Failed to read paired devices."
                if paired_devices:
                    _, name = next(iter(paired_devices.values()))
                    alert_msg = f"Paired to {name}"
                    ok = True
                elif paired_devices is not None:
                    alias = self.bluetooth_alias() or ""
                    try:
                        g_vars["disable_keys"] = True
                        cmd = ["systemctl", "start", "bt-timedpair"]
                        subprocess.run(cmd).check_returncode()
                        alert_msg = 'Bluetooth is on. Discoverable as "' + alias + '"'
                        ok = True
                    except Exception:
                        alert_msg = "Failed to set as discoverable."
                    finally:
                        g_vars["disable_keys"] = False

        else:
            alert_msg = "Failed to turn on bluetooth."

        if alert_msg is not None:
            if ok:
                self.alert_obj.display_alert_info(g_vars, alert_msg, title="Success")
            else:
                self.alert_obj.display_alert_error(g_vars, alert_msg)

        g_vars["display_state"] = "page"

    def bluetooth_on(self, g_vars):
        if not self.bluetooth_present():
            self.alert_obj.display_alert_error(g_vars, "Bluetooth adapter not found.")
            g_vars["display_state"] = "page"
            return

        ok = False
        if self.bluetooth_set_power(True):
            alert_msg = "Bluetooth is on."
            ok = True
        else:
            alert_msg = "Failed to turn on bluetooth."

        if ok:
            self.alert_obj.display_alert_info(g_vars, alert_msg, title="Success")
        else:
            self.alert_obj.display_alert_error(g_vars, alert_msg)

        g_vars["display_state"] = "page"

    def bluetooth_off(self, g_vars):
        if not self.bluetooth_present():
            self.alert_obj.display_alert_error(g_vars, "Bluetooth adapter not found.")
            g_vars["display_state"] = "page"
            return

        ok = False
        if self.bluetooth_set_power(False):
            alert_msg = "Bluetooth is off."
            ok = True
        else:
            alert_msg = "Failed to turn off bluetooth."

        if ok:
            self.alert_obj.display_alert_info(g_vars, alert_msg, title="Success")
        else:
            self.alert_obj.display_alert_error(g_vars, alert_msg)

        g_vars["display_state"] = "page"
