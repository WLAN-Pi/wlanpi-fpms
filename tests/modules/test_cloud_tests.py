import pytest
import sys


@pytest.fixture
def patch_imports():
    sys.modules["fpms.modules.pages.alert"] = __import__("fakes")
    sys.modules["fpms.modules.pages.simpletable"] = __import__("fakes")


def test_test_mist_cloud_cached(patch_imports):
    """Tests the fall through if the results cached value is true"""
    # Arrange
    from fpms.modules.cloud_tests import CloudUtils

    test_g_vars = {"result_cache": True}
    # Act
    test_object = CloudUtils(g_vars=test_g_vars)
    test_object.test_mist_cloud(test_g_vars)
    # Assert
    # If g_vars["result_cache"] is True then
    # self.alert_obj.display_popup_alert is never called
    # so we look to see that the running arg is not stored
    # FIXME: This test shows that this method should probably be refactored
    with pytest.raises(ValueError):
        index = test_object.alert_obj.args.index("Running...")


def test_test_mist_cloud_all_checks_pass(patch_imports, monkeypatch):
    """Tests if port is up, ip is present, dns is ok, and call returns 200"""
    # Arrange
    from fpms.modules.cloud_tests import CloudUtils

    test_g_vars = {"result_cache": False}
    test_link_state = {"set": "yes", "expected": "Eth0 Port Up: YES"}
    test_ip = {"set": "192.0.2.1", "expected": "MyIP: 192.0.2.1"}
    test_return_code = {"set": "200", "expected": "HTTP: OK"}
    test_socket = {"set": True, "expected": "DNS: OK"}

    def faked_eth0(*args, **kwargs):
        if args[0] == "/sbin/ethtool eth0 | grep 'Link detected'| awk '{print $3}'":
            return test_link_state["set"].encode("utf-8")
        if (
            args[0]
            == "ip address show eth0 | grep 'inet ' | awk '{print $2}' | awk -F'/' '{print $1}'"
        ):
            return test_ip["set"].encode("utf-8")
        if (
            args[0]
            == 'curl -k -s -o /dev/null -w "%{http_code}" https://ep-terminator.mistsys.net/test'
        ):
            return test_return_code["set"].encode("utf-8")

    def faked_socket(*args, **kwargs):
        if args[0] == "ep-terminator.mistsys.net":
            test_socket["set"]

    monkeypatch.setattr("subprocess.check_output", faked_eth0)
    monkeypatch.setattr("socket.gethostbyname", faked_socket)

    # Act
    test_object = CloudUtils(g_vars=test_g_vars)
    test_object.test_mist_cloud(test_g_vars)
    # Assert
    assert test_object.simple_table_obj.args == (
        {"result_cache": True, "disable_keys": False},
        [
            test_link_state["expected"],
            test_ip["expected"],
            test_socket["expected"],
            test_return_code["expected"],
        ],
    )
    assert test_object.simple_table_obj.kwargs == {"title": "Mist Cloud"}


@pytest.mark.parametrize(
    "nic_state", [("no", "Eth0 Port Up: NO"), ("BROKEN", "Eth0 Port Up: Unknown")]
)
def test_test_mist_cloud_eth0_down(patch_imports, monkeypatch, nic_state):
    """Tests if eth0 is not up or unknown value comes back"""
    # Arrange
    from fpms.modules.cloud_tests import CloudUtils

    test_g_vars = {"result_cache": False}
    test_link_state = {"set": nic_state[0], "expected": nic_state[1]}

    def faked_eth0(*args, **kwargs):
        if args[0] == "/sbin/ethtool eth0 | grep 'Link detected'| awk '{print $3}'":
            return test_link_state["set"].encode("utf-8")

    monkeypatch.setattr("subprocess.check_output", faked_eth0)

    # Act
    test_object = CloudUtils(g_vars=test_g_vars)
    test_object.test_mist_cloud(test_g_vars)
    # Assert
    assert test_object.simple_table_obj.args == (
        {"result_cache": True, "disable_keys": False},
        [test_link_state["expected"], "", "", ""],
    )
    assert test_object.simple_table_obj.kwargs == {"title": "Mist Cloud"}


def test_test_mist_cloud_eth0_up_no_ip(patch_imports, monkeypatch):
    """Tests if eth0 is up but there is no IP"""
    # Arrange
    from fpms.modules.cloud_tests import CloudUtils

    test_g_vars = {"result_cache": False}
    test_link_state = {"set": "yes", "expected": "Eth0 Port Up: YES"}
    test_ip = {"set": "", "expected": "MyIP: None"}

    def faked_eth0(*args, **kwargs):
        if args[0] == "/sbin/ethtool eth0 | grep 'Link detected'| awk '{print $3}'":
            return test_link_state["set"].encode("utf-8")
        if (
            args[0]
            == "ip address show eth0 | grep 'inet ' | awk '{print $2}' | awk -F'/' '{print $1}'"
        ):
            return test_ip["set"].encode("utf-8")

    monkeypatch.setattr("subprocess.check_output", faked_eth0)

    # Act
    test_object = CloudUtils(g_vars=test_g_vars)
    test_object.test_mist_cloud(test_g_vars)
    # Assert
    assert test_object.simple_table_obj.args == (
        {"result_cache": True, "disable_keys": False},
        [
            test_link_state["expected"],
            test_ip["expected"],
            "",
            "",
        ],
    )
    assert test_object.simple_table_obj.kwargs == {"title": "Mist Cloud"}


def test_test_mist_cloud_eth0_up_has_ip_no_dns(patch_imports, monkeypatch):
    """Tests if eth0 is up and has an IP but DNS fails"""
    # Arrange
    from fpms.modules.cloud_tests import CloudUtils

    test_g_vars = {"result_cache": False}
    test_link_state = {"set": "yes", "expected": "Eth0 Port Up: YES"}
    test_ip = {"set": "192.0.2.1", "expected": "MyIP: 192.0.2.1"}
    test_socket = {"expected": "DNS: FAIL"}

    def faked_eth0(*args, **kwargs):
        if args[0] == "/sbin/ethtool eth0 | grep 'Link detected'| awk '{print $3}'":
            return test_link_state["set"].encode("utf-8")
        if (
            args[0]
            == "ip address show eth0 | grep 'inet ' | awk '{print $2}' | awk -F'/' '{print $1}'"
        ):
            return test_ip["set"].encode("utf-8")

    def faked_socket(*args, **kwargs):
        if args[0] == "ep-terminator.mistsys.net":
            raise Exception

    monkeypatch.setattr("subprocess.check_output", faked_eth0)
    monkeypatch.setattr("socket.gethostbyname", faked_socket)

    # Act
    test_object = CloudUtils(g_vars=test_g_vars)
    test_object.test_mist_cloud(test_g_vars)
    # Assert
    assert test_object.simple_table_obj.args == (
        {"result_cache": True, "disable_keys": False},
        [
            test_link_state["expected"],
            test_ip["expected"],
            test_socket["expected"],
            "",
        ],
    )
    assert test_object.simple_table_obj.kwargs == {"title": "Mist Cloud"}


def test_test_mist_cloud_eth0_up_has_ip_has_dns_no_200(patch_imports, monkeypatch):
    """Tests if eth0 is up, has an IP, has DNS, but does not get 200 back"""
    # Arrange
    from fpms.modules.cloud_tests import CloudUtils

    test_g_vars = {"result_cache": False}
    test_link_state = {"set": "yes", "expected": "Eth0 Port Up: YES"}
    test_ip = {"set": "192.0.2.1", "expected": "MyIP: 192.0.2.1"}
    test_return_code = {"set": "418", "expected": "HTTP: FAIL"}
    test_socket = {"set": True, "expected": "DNS: OK"}

    def faked_eth0(*args, **kwargs):
        if args[0] == "/sbin/ethtool eth0 | grep 'Link detected'| awk '{print $3}'":
            return test_link_state["set"].encode("utf-8")
        if (
            args[0]
            == "ip address show eth0 | grep 'inet ' | awk '{print $2}' | awk -F'/' '{print $1}'"
        ):
            return test_ip["set"].encode("utf-8")
        if (
            args[0]
            == 'curl -k -s -o /dev/null -w "%{http_code}" https://ep-terminator.mistsys.net/test'
        ):
            return test_return_code["set"].encode("utf-8")

    def faked_socket(*args, **kwargs):
        if args[0] == "ep-terminator.mistsys.net":
            test_socket["set"]

    monkeypatch.setattr("subprocess.check_output", faked_eth0)
    monkeypatch.setattr("socket.gethostbyname", faked_socket)

    # Act
    test_object = CloudUtils(g_vars=test_g_vars)
    test_object.test_mist_cloud(test_g_vars)
    # Assert
    assert test_object.simple_table_obj.args == (
        {"result_cache": True, "disable_keys": False},
        [
            test_link_state["expected"],
            test_ip["expected"],
            test_socket["expected"],
            test_return_code["expected"],
        ],
    )
    assert test_object.simple_table_obj.kwargs == {"title": "Mist Cloud"}
