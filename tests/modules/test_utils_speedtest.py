from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from fpms.modules.utils import Utils


def test_parse_librespeed_v1_0_14_output():
    output = (
        Path(__file__).parents[1] / "fixtures/librespeed-cli-v1.0.14.stdout"
    ).read_text()

    assert Utils.parse_librespeed_output(output) == [
        "Ping: 17.39 ms",
        "D: 766.38 Mbps",
        "U: 509.15 Mbps",
    ]


def test_show_speedtest_runs_librespeed_with_timeout(monkeypatch):
    output = (
        Path(__file__).parents[1] / "fixtures/librespeed-cli-v1.0.14.stdout"
    ).read_text()
    run = Mock(return_value=SimpleNamespace(stdout=output))
    monkeypatch.setattr("subprocess.run", run)
    monkeypatch.setattr(
        Utils, "speedtest_cli_path", staticmethod(lambda: "/usr/bin/librespeed-cli")
    )
    g_vars = {"result_cache": False, "disable_keys": False}

    speedtest = Utils(g_vars)
    speedtest.show_speedtest(g_vars)

    run.assert_called_once_with(
        ["/usr/bin/librespeed-cli", "--json", "--simple"],
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )
    assert speedtest.simple_table_obj.args == (
        g_vars,
        ["Ping: 17.39 ms", "D: 766.38 Mbps", "U: 509.15 Mbps"],
    )
