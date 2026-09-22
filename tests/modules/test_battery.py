from fpms.modules.battery import Battery


def make_battery(info):
    # Bypass __init__ so we don't touch the sysfs battery file.
    battery = Battery.__new__(Battery)
    battery.info = info
    return battery


def test_battery_absent_reports_zero():
    battery = make_battery({"POWER_SUPPLY_PRESENT": "0"})
    assert battery.battery_present() is False
    assert battery.battery_charge() == 0
    assert battery.battery_voltage() == 0
    assert battery.battery_cycle_count() == 0


def test_battery_charge_clamps_to_voltage_range():
    full = make_battery(
        {"POWER_SUPPLY_PRESENT": "1", "POWER_SUPPLY_VOLTAGE_NOW": "4100000"}
    )
    empty = make_battery(
        {"POWER_SUPPLY_PRESENT": "1", "POWER_SUPPLY_VOLTAGE_NOW": "3300000"}
    )
    assert full.battery_charge() == 100
    assert empty.battery_charge() == 0


def test_battery_charge_midpoint():
    battery = make_battery(
        {"POWER_SUPPLY_PRESENT": "1", "POWER_SUPPLY_VOLTAGE_NOW": "3700000"}
    )
    assert battery.battery_charge() == 50


def test_battery_voltage_status_and_cycles():
    battery = make_battery(
        {
            "POWER_SUPPLY_PRESENT": "1",
            "POWER_SUPPLY_VOLTAGE_NOW": "3700000",
            "POWER_SUPPLY_STATUS": "Discharging",
            "POWER_SUPPLY_CYCLE_COUNT": "7",
        }
    )
    assert battery.battery_voltage() == 3700000
    assert battery.battery_status() == "discharging"
    assert battery.battery_cycle_count() == 7
